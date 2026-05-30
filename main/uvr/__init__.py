"""
main.uvr – Audio separation sub-package (Ultimate Vocal Remover / Roformer).

Contains the individual separation steps used in the Hyper-RVC pipeline:
vocal separation, karaoke separation, dereverb, deecho, and denoise.
"""

from main.uvr.separator import (  # noqa: F401
    separate_vocals,
    separate_karaoke,
    remove_reverb,
    remove_echo,
    remove_noise,
)
