"""
Shared utility functions for the Hyper-RVC predictor subsystem.

Ported from Vietnamese-RVC (https://github.com/PhamHuynhAnh16/Vietnamese-RVC).
Only the functions required by the F0 Generator (autotune, proposal pitch,
circular buffer) are included here.
"""

import numpy as np
import torch


def extract_median_f0(f0: np.ndarray) -> float:
    """Compute the median F0 value, ignoring silence frames (f0 == 0).

    Args:
        f0: 1-D numpy array of F0 values in Hz (0 = unvoiced).

    Returns:
        Median F0 in Hz as a float.
    """
    f0 = np.where(f0 == 0, np.nan, f0)
    return float(
        np.median(
            np.interp(
                np.arange(len(f0)),
                np.where(~np.isnan(f0))[0],
                f0[~np.isnan(f0)],
            )
        )
    )


def autotune_f0(note_dict, f0, f0_autotune_strength):
    """Snap F0 values to the nearest note in *note_dict*.

    Args:
        note_dict: Sorted list (or array) of reference note frequencies.
        f0: 1-D numpy array of F0 values in Hz.
        f0_autotune_strength: Blend factor (0 = no autotune, 1 = full snap).

    Returns:
        1-D numpy array of autotuned F0 values.
    """
    autotuned_f0 = np.zeros_like(f0)
    for i, freq in enumerate(f0):
        autotuned_f0[i] = freq + (
            min(note_dict, key=lambda x: abs(x - freq)) - freq
        ) * f0_autotune_strength
    return autotuned_f0


def proposal_f0_up_key(f0, target_f0=155.0, limit=12):
    """Propose an F0 up-key shift so the median pitch lands near *target_f0*.

    Args:
        f0: 1-D numpy array of F0 values in Hz.
        target_f0: Desired median F0 in Hz (default 155 Hz, roughly D3).
        limit: Maximum semitone shift (default ±12).

    Returns:
        Integer number of semitones to shift (clamped to [-limit, limit]).
    """
    try:
        return max(
            -limit,
            min(limit, int(np.round(12 * np.log2(target_f0 / extract_median_f0(f0))))),
        )
    except ValueError:
        return 0


def circular_write(new_data, target):
    """Shift *target* left by len(new_data) and append *new_data* at the end.

    Used by the realtime inference loop to maintain a circular pitch buffer.

    Args:
        new_data: 1-D torch tensor of new pitch values.
        target: 1-D torch tensor (modified in-place) serving as the buffer.

    Returns:
        The updated *target* tensor.
    """
    offset = new_data.shape[0]
    target[:-offset] = target[offset:].detach().clone()
    target[-offset:] = new_data
    return target
