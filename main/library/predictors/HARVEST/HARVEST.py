"""
HARVEST F0 predictor for Hyper-RVC.

Uses pyworld for F0 estimation (harvest algorithm).
"""

import numpy as np


class HARVEST:
    """HARVEST F0 predictor using pyworld.

    Args:
        f0_min: Minimum F0 to detect in Hz.
        f0_max: Maximum F0 to detect in Hz.
        sample_rate: Audio sample rate.
    """

    def __init__(self, f0_min=50.0, f0_max=1100.0, sample_rate=16000):
        try:
            import pyworld
            self._pyworld = pyworld
        except ImportError:
            raise ImportError(
                "pyworld is required for HARVEST F0 prediction. "
                "Install it with: pip install pyworld"
            )
        self.f0_min = f0_min
        self.f0_max = f0_max
        self.sample_rate = sample_rate

    def infer_from_audio(self, audio, thred=0.03):
        """Estimate F0 from audio using HARVEST.

        Args:
            audio: 1-D numpy array of audio samples at self.sample_rate.
            thred: Unused (kept for API compatibility).

        Returns:
            1-D numpy array of F0 values in Hz.
        """
        audio = audio.astype(np.float64)
        f0, _ = self._pyworld.harvest(
            audio, self.sample_rate,
            f0_floor=self.f0_min,
            f0_ceil=self.f0_max,
        )
        return f0.astype(np.float32)

    def infer_from_audio_with_pitch(self, audio, thred=0.03, f0_min=50, f0_max=1100):
        """Estimate F0 with explicit pitch range filtering.

        Args:
            audio: 1-D numpy array of audio samples.
            thred: Unused.
            f0_min: Minimum F0 in Hz.
            f0_max: Maximum F0 in Hz.

        Returns:
            1-D numpy array of F0 values in Hz.
        """
        audio = audio.astype(np.float64)
        f0, _ = self._pyworld.harvest(
            audio, self.sample_rate,
            f0_floor=f0_min,
            f0_ceil=f0_max,
        )
        return f0.astype(np.float32)
