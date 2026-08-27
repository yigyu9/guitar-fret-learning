import torch
import torchaudio
import warnings
from nnAudio.Spectrogram import CQT1992v2

class AudioFeatureExtractor:
    def __init__(self, sr=22050, hop_length=256, n_bins=288, bins_per_octave=36):
        self.sr = sr
        self.hop_length = hop_length
        self.n_bins = n_bins
        self.bins_per_octave = bins_per_octave
        self.fps = sr / hop_length
        
        self.cqt_layer = CQT1992v2(
            sr=sr, 
            hop_length=hop_length, 
            n_bins=n_bins, 
            bins_per_octave=bins_per_octave, 
            output_format='Magnitude',
            trainable=False
        )

    def load_audio(self, audio_path):
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            
            if sample_rate != self.sr:
                resampler = torchaudio.transforms.Resample(sample_rate, self.sr)
                waveform = resampler(waveform)
            
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            min_length = 33000 
            if waveform.shape[-1] < min_length:
                pad_len = min_length - waveform.shape[-1]
                waveform = torch.nn.functional.pad(waveform, (0, pad_len), mode='constant', value=0)
                
            return waveform 

        except Exception as e:
            return None