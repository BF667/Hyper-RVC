"""
Speaker embedding extraction using pretrained models.

Provides interface for extracting speaker embeddings from audio waveforms.
"""

import os
import sys
import torch
import logging

import numpy as np
import torch.nn.functional as F

from functools import cached_property
from torch.nn.utils.rnn import pad_sequence
from typing import Optional, Tuple

sys.path.append(os.getcwd())

from main.whisper.diarization.speechbrain import EncoderClassifier
from main.tools.logger import get_logger

logger = get_logger(__name__)


class SpeechBrainPretrainedSpeakerEmbedding:
    """
    Extract speaker embeddings using SpeechBrain pretrained models.
    
    Supports various embedding models like ECAPA-TDNN.
    """
    def __init__(
        self,
        embedding: str,
        device: Optional[str] = None
    ):
        """
        Initialize speaker embedding extractor.
        
        Args:
            embedding: Name of the embedding model to use
            device: Device to run inference on
        """
        super().__init__()

        self.embedding = embedding
        self.device = device or torch.device("cpu")
        logger.info(f"Initializing SpeechBrain embedding model: {embedding}")
        
        self.classifier_ = EncoderClassifier.from_hparams(
            source=self.embedding,
            run_opts={"device": self.device}
        )
        logger.info(f"Speaker embedding model loaded on {self.device}")

    @cached_property
    def dimension(self):
        *_, dimension = self.classifier_.encode_batch(
            torch.rand(1, 16000).to(self.device)
        ).shape

        return dimension

    @cached_property
    def min_num_samples(self):
        with torch.inference_mode():
            lower, upper = 2, round(0.5 * self.classifier_.audio_normalizer.sample_rate)
            middle = (lower + upper) // 2

            while lower + 1 < upper:
                try:
                    _ = self.classifier_.encode_batch(torch.randn(1, middle).to(self.device))
                    upper = middle
                except RuntimeError:
                    lower = middle

                middle = (lower + upper) // 2

        return upper

    def __call__(self, waveforms, masks = None):
        batch_size, num_channels, num_samples = waveforms.shape
        assert num_channels == 1

        waveforms = waveforms.squeeze(dim=1)

        if masks is None:
            signals = waveforms.squeeze(dim=1)
            wav_lens = signals.shape[1] * torch.ones(batch_size)
        else:
            batch_size_masks, _ = masks.shape
            assert batch_size == batch_size_masks

            imasks = F.interpolate(
                masks.unsqueeze(dim=1), 
                size=num_samples, 
                mode="nearest"
            ).squeeze(dim=1) > 0.5

            signals = pad_sequence([
                waveform[imask].contiguous() 
                for waveform, imask in zip(waveforms, imasks)
            ], batch_first=True)
    
            wav_lens = imasks.sum(dim=1)

        max_len = wav_lens.max()
        if max_len < self.min_num_samples: return np.nan * np.zeros((batch_size, self.dimension))

        too_short = wav_lens < self.min_num_samples
        wav_lens = wav_lens / max_len
        wav_lens[too_short] = 1.0

        embeddings = (
            self.classifier_.encode_batch(
                signals, 
                wav_lens=wav_lens
            ).squeeze(dim=1).cpu().numpy()
        )

        embeddings[too_short.cpu().numpy()] = np.nan
        return embeddings
