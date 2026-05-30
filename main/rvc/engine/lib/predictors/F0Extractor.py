import dataclasses
import pathlib
import libf0
import librosa
import numpy as np
import resampy
import torch
import torchcrepe
import torchfcpe
import os

from main.rvc.engine.configs.config import Config
from main.library.predictors.Generator import F0Generator
from main.tools.variables import get_f0_defaults

config = Config()


@dataclasses.dataclass
class F0Extractor:
    wav_path: pathlib.Path
    sample_rate: int = 44100
    hop_length: int = 512
    f0_min: int = 50
    f0_max: int = 1600
    method: str = "rmvpe"
    x: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self):
        self.x, self.sample_rate = librosa.load(self.wav_path, sr=self.sample_rate)
        # Fall back to CPU for ZLUDA as these methods use CUcFFT
        device = (
            "cpu"
            if "cuda" in config.device
            and torch.cuda.get_device_name().endswith("[ZLUDA]")
            else config.device
        )
        self._device = device
        self._f0_gen = F0Generator(
            device=device,
            is_half=False if device == "cpu" else config.is_half,
            f0_min=self.f0_min,
            f0_max=self.f0_max,
            sample_rate=self.sample_rate,
        )

    @property
    def hop_size(self) -> float:
        return self.hop_length / self.sample_rate

    @property
    def wav16k(self) -> np.ndarray:
        return resampy.resample(self.x, self.sample_rate, 16000)

    def extract_f0(self) -> np.ndarray:
        method = self.method
        f0_defaults = get_f0_defaults()

        if method == "crepe":
            wav16k_torch = torch.FloatTensor(self.wav16k).unsqueeze(0).to(self._device)
            f0 = torchcrepe.predict(
                wav16k_torch,
                sample_rate=16000,
                hop_length=160,
                batch_size=512,
                fmin=self.f0_min,
                fmax=self.f0_max,
                device=self._device,
            )
            f0 = f0[0].cpu().numpy()
        elif method == "fcpe":
            audio = librosa.to_mono(self.x)
            audio_length = len(audio)
            f0_target_length = (audio_length // self.hop_length) + 1
            audio = (
                torch.from_numpy(audio).float().unsqueeze(0).unsqueeze(-1).to(self._device)
            )
            model = torchfcpe.spawn_bundled_infer_model(device=self._device)

            f0 = model.infer(
                audio,
                sr=self.sample_rate,
                decoder_mode="local_argmax",
                threshold=0.006,
                f0_min=self.f0_min,
                f0_max=self.f0_max,
                interp_uv=False,
                output_interp_target_length=f0_target_length,
            )
            f0 = f0.squeeze().cpu().numpy()
        elif method in ("rmvpe", "onnxcrepe", "harvest"):
            f0 = self._f0_gen.get_f0(
                self.wav16k,
                p_len=None,
                f0_method=method,
                filter_radius=f0_defaults.get("rmvpe_threshold", 3.0) * 100,
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")
        return libf0.hz_to_cents(f0, librosa.midi_to_hz(0))

    def plot_f0(self, f0):
        from matplotlib import pyplot as plt

        plt.figure(figsize=(10, 4))
        plt.plot(f0)
        plt.title(self.method)
        plt.xlabel("Time (frames)")
        plt.ylabel("F0 (cents)")
        plt.show()
