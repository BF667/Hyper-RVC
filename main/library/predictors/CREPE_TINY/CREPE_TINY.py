"""
CREPE-tiny F0 predictor for Hyper-RVC.

This is a thin subclass of :class:`CREPE` that defaults to the smaller,
faster ``"tiny"`` model variant while keeping the same public API.
"""

from main.library.predictors.CREPE.CREPE import CREPE


class CREPE_TINY(CREPE):
    """CREPE-tiny F0 predictor (smaller, faster model).

    Parameters
    ----------
    model_path : str
        Path to the model weights (``.pt`` or ``.onnx``).
    device : str or None
        Torch device when *onnx=False*.
    is_half : bool
        If *True*, cast the PyTorch model to ``float16`` on CUDA.
    onnx : bool
        When *True*, load the model with onnxruntime.
    providers : list[str] or None
        Optional ONNX execution providers.
    hop_length : int
        Hop length in samples at *sample_rate*.
    f0_min : float
        Minimum detectable F0 in Hz.
    f0_max : float
        Maximum detectable F0 in Hz.
    sample_rate : int
        Expected audio sample rate (internally resampled to 16 kHz).
    """

    def __init__(
        self,
        model_path,
        device=None,
        is_half=False,
        onnx=False,
        providers=None,
        hop_length=512,
        f0_min=50,
        f0_max=1100,
        sample_rate=16000,
    ):
        super().__init__(
            model_path,
            device=device,
            is_half=is_half,
            onnx=onnx,
            providers=providers,
            model_size="tiny",
            hop_length=hop_length,
            f0_min=f0_min,
            f0_max=f0_max,
            sample_rate=sample_rate,
        )
