"""
Lions Flute Audio Processing Engine
Real audio processing capabilities for splitting and effects
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from scipy import signal
import tempfile
import time
from typing import Tuple, Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Advanced audio processing engine for Lions Flute."""
    
    def __init__(self, upload_folder: str = 'uploads'):
        self.upload_folder = upload_folder
        self.processed_folder = os.path.join(upload_folder, 'processed')
        os.makedirs(self.processed_folder, exist_ok=True)
        
    def load_audio(self, filename: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate."""
        filepath = os.path.join(self.upload_folder, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filename}")
        
        # Load with librosa for better format support
        try:
            audio_data, sample_rate = librosa.load(filepath, sr=None, mono=False)
            logger.info(f"Loaded audio: {filename}, shape: {audio_data.shape}, sr: {sample_rate}")
            return audio_data, sample_rate
        except Exception as e:
            logger.error(f"Error loading audio {filename}: {str(e)}")
            raise
    
    def save_audio(self, audio_data: np.ndarray, sample_rate: int, output_filename: str) -> str:
        """Save processed audio to file."""
        output_path = os.path.join(self.processed_folder, output_filename)
        
        try:
            # Ensure audio is in the right format
            if len(audio_data.shape) == 1:
                # Mono audio
                sf.write(output_path, audio_data, sample_rate)
            else:
                # Stereo audio - transpose for soundfile
                sf.write(output_path, audio_data.T, sample_rate)
            
            logger.info(f"Saved processed audio: {output_filename}")
            return output_filename
        except Exception as e:
            logger.error(f"Error saving audio {output_filename}: {str(e)}")
            raise
    
    def split_vocals_instruments(self, filename: str) -> Dict[str, str]:
        """
        Advanced vocal/instrumental separation using spectral subtraction
        and harmonic-percussive separation.
        """
        try:
            logger.info(f"Starting vocal separation for: {filename}")
            
            # Load audio
            audio_data, sample_rate = self.load_audio(filename)
            
            # Convert to mono if stereo for processing
            if len(audio_data.shape) > 1:
                audio_mono = np.mean(audio_data, axis=0)
            else:
                audio_mono = audio_data
            
            # Use librosa's harmonic-percussive separation
            harmonic, percussive = librosa.effects.hpss(audio_mono, margin=8)
            
            # Advanced vocal isolation using spectral subtraction
            stft = librosa.stft(audio_mono, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Create masks for vocals and instruments
            # Vocals typically have strong harmonic content in mid frequencies
            freq_bins = magnitude.shape[0]
            vocal_mask = np.ones_like(magnitude)
            instrumental_mask = np.ones_like(magnitude)
            
            # Enhance vocal frequencies (roughly 300Hz - 3000Hz)
            vocal_freq_start = int(300 * freq_bins / (sample_rate / 2))
            vocal_freq_end = int(3000 * freq_bins / (sample_rate / 2))
            
            # Create frequency-based separation
            for i in range(freq_bins):
                if vocal_freq_start <= i <= vocal_freq_end:
                    # Boost vocals in vocal range
                    vocal_mask[i, :] *= 1.5
                    instrumental_mask[i, :] *= 0.3
                else:
                    # Reduce vocals outside vocal range
                    vocal_mask[i, :] *= 0.4
                    instrumental_mask[i, :] *= 1.2
            
            # Apply masks
            vocal_stft = magnitude * vocal_mask * np.exp(1j * phase)
            instrumental_stft = magnitude * instrumental_mask * np.exp(1j * phase)
            
            # Convert back to time domain
            vocals = librosa.istft(vocal_stft, hop_length=512)
            instruments = librosa.istft(instrumental_stft, hop_length=512)
            
            # Normalize audio
            vocals = vocals / np.max(np.abs(vocals)) * 0.8
            instruments = instruments / np.max(np.abs(instruments)) * 0.8
            
            # Generate output filenames
            base_name = os.path.splitext(filename)[0]
            vocals_filename = f"{base_name}_vocals.wav"
            instruments_filename = f"{base_name}_instruments.wav"
            
            # Save separated audio
            self.save_audio(vocals, sample_rate, vocals_filename)
            self.save_audio(instruments, sample_rate, instruments_filename)
            
            logger.info(f"Vocal separation completed for: {filename}")
            
            return {
                'vocals': vocals_filename,
                'instruments': instruments_filename,
                'original': filename,
                'sample_rate': sample_rate
            }
            
        except Exception as e:
            logger.error(f"Vocal separation error for {filename}: {str(e)}")
            raise
    
    def apply_reverb(self, audio_data: np.ndarray, sample_rate: int, 
                    room_size: float = 0.5, damping: float = 0.5, 
                    wet_level: float = 0.3) -> np.ndarray:
        """Apply reverb effect using convolution with impulse response."""
        try:
            # Create a simple impulse response for reverb
            reverb_time = room_size * 2.0  # seconds
            reverb_samples = int(reverb_time * sample_rate)
            
            # Generate exponentially decaying noise as impulse response
            impulse = np.random.normal(0, 1, reverb_samples) * np.exp(-np.arange(reverb_samples) / (reverb_samples * damping))
            impulse = impulse / np.max(np.abs(impulse))
            
            # Apply convolution
            if len(audio_data.shape) == 1:
                # Mono
                reverb_audio = signal.convolve(audio_data, impulse, mode='same')
            else:
                # Stereo
                reverb_audio = np.zeros_like(audio_data)
                for i in range(audio_data.shape[0]):
                    reverb_audio[i] = signal.convolve(audio_data[i], impulse, mode='same')
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + reverb_audio * wet_level
            
        except Exception as e:
            logger.error(f"Reverb processing error: {str(e)}")
            raise
    
    def apply_echo(self, audio_data: np.ndarray, sample_rate: int, 
                   delay: float = 0.3, decay: float = 0.5, 
                   wet_level: float = 0.4) -> np.ndarray:
        """Apply echo effect."""
        try:
            delay_samples = int(delay * sample_rate)
            
            if len(audio_data.shape) == 1:
                # Mono
                echo_audio = np.zeros(len(audio_data) + delay_samples)
                echo_audio[:len(audio_data)] = audio_data
                echo_audio[delay_samples:delay_samples + len(audio_data)] += audio_data * decay
                echo_audio = echo_audio[:len(audio_data)]
            else:
                # Stereo
                echo_audio = np.zeros_like(audio_data)
                for i in range(audio_data.shape[0]):
                    temp = np.zeros(len(audio_data[i]) + delay_samples)
                    temp[:len(audio_data[i])] = audio_data[i]
                    temp[delay_samples:delay_samples + len(audio_data[i])] += audio_data[i] * decay
                    echo_audio[i] = temp[:len(audio_data[i])]
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + echo_audio * wet_level
            
        except Exception as e:
            logger.error(f"Echo processing error: {str(e)}")
            raise
    
    def apply_chorus(self, audio_data: np.ndarray, sample_rate: int, 
                     rate: float = 1.5, depth: float = 0.002, 
                     wet_level: float = 0.5) -> np.ndarray:
        """Apply chorus effect using delayed modulated signals."""
        try:
            # Create LFO (Low Frequency Oscillator)
            length = len(audio_data) if len(audio_data.shape) == 1 else len(audio_data[0])
            time_axis = np.arange(length) / sample_rate
            lfo = np.sin(2 * np.pi * rate * time_axis) * depth * sample_rate
            
            if len(audio_data.shape) == 1:
                # Mono
                chorus_audio = np.zeros_like(audio_data)
                for i, delay_mod in enumerate(lfo):
                    delay_idx = max(0, i - int(delay_mod))
                    if delay_idx < len(audio_data):
                        chorus_audio[i] = audio_data[delay_idx]
            else:
                # Stereo
                chorus_audio = np.zeros_like(audio_data)
                for ch in range(audio_data.shape[0]):
                    for i, delay_mod in enumerate(lfo):
                        delay_idx = max(0, i - int(delay_mod))
                        if delay_idx < len(audio_data[ch]):
                            chorus_audio[ch][i] = audio_data[ch][delay_idx]
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + chorus_audio * wet_level
            
        except Exception as e:
            logger.error(f"Chorus processing error: {str(e)}")
            raise
    
    def apply_distortion(self, audio_data: np.ndarray, gain: float = 2.0, 
                        wet_level: float = 0.6) -> np.ndarray:
        """Apply distortion effect using waveshaping."""
        try:
            # Apply gain and clip
            gained_audio = audio_data * gain
            distorted = np.tanh(gained_audio)  # Soft clipping
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + distorted * wet_level
            
        except Exception as e:
            logger.error(f"Distortion processing error: {str(e)}")
            raise
    
    def apply_compressor(self, audio_data: np.ndarray, threshold: float = 0.5, 
                        ratio: float = 4.0, wet_level: float = 0.8) -> np.ndarray:
        """Apply dynamic range compression."""
        try:
            # Simple compressor implementation
            compressed = np.copy(audio_data)
            
            if len(audio_data.shape) == 1:
                # Mono
                mask = np.abs(audio_data) > threshold
                compressed[mask] = threshold + (audio_data[mask] - threshold) / ratio
            else:
                # Stereo
                for ch in range(audio_data.shape[0]):
                    mask = np.abs(audio_data[ch]) > threshold
                    compressed[ch][mask] = threshold + (audio_data[ch][mask] - threshold) / ratio
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + compressed * wet_level
            
        except Exception as e:
            logger.error(f"Compressor processing error: {str(e)}")
            raise
    
    def apply_equalizer(self, audio_data: np.ndarray, sample_rate: int, 
                       low_gain: float = 1.0, mid_gain: float = 1.0, 
                       high_gain: float = 1.0, wet_level: float = 0.7) -> np.ndarray:
        """Apply 3-band equalizer."""
        try:
            # Define frequency bands
            low_freq = 300   # Hz
            high_freq = 3000 # Hz
            
            # Design filters
            nyquist = sample_rate / 2
            low_cutoff = low_freq / nyquist
            high_cutoff = high_freq / nyquist
            
            # Low-pass filter for low frequencies
            b_low, a_low = signal.butter(4, low_cutoff, btype='low')
            
            # Band-pass filter for mid frequencies  
            b_mid, a_mid = signal.butter(4, [low_cutoff, high_cutoff], btype='band')
            
            # High-pass filter for high frequencies
            b_high, a_high = signal.butter(4, high_cutoff, btype='high')
            
            if len(audio_data.shape) == 1:
                # Mono
                low_band = signal.filtfilt(b_low, a_low, audio_data) * low_gain
                mid_band = signal.filtfilt(b_mid, a_mid, audio_data) * mid_gain
                high_band = signal.filtfilt(b_high, a_high, audio_data) * high_gain
                eq_audio = low_band + mid_band + high_band
            else:
                # Stereo
                eq_audio = np.zeros_like(audio_data)
                for ch in range(audio_data.shape[0]):
                    low_band = signal.filtfilt(b_low, a_low, audio_data[ch]) * low_gain
                    mid_band = signal.filtfilt(b_mid, a_mid, audio_data[ch]) * mid_gain
                    high_band = signal.filtfilt(b_high, a_high, audio_data[ch]) * high_gain
                    eq_audio[ch] = low_band + mid_band + high_band
            
            # Mix dry and wet signals
            return audio_data * (1 - wet_level) + eq_audio * wet_level
            
        except Exception as e:
            logger.error(f"Equalizer processing error: {str(e)}")
            raise
    
    def apply_effect(self, filename: str, effect_name: str, intensity: float = 50) -> str:
        """Apply the specified audio effect."""
        try:
            logger.info(f"Applying {effect_name} effect to {filename} (intensity: {intensity}%)")
            
            # Load audio
            audio_data, sample_rate = self.load_audio(filename)
            
            # Normalize intensity (0-100 to 0-1)
            intensity_normalized = intensity / 100.0
            
            # Apply the requested effect
            if effect_name.lower() == 'reverb':
                processed_audio = self.apply_reverb(
                    audio_data, sample_rate, 
                    room_size=intensity_normalized, 
                    wet_level=intensity_normalized * 0.5
                )
            elif effect_name.lower() == 'echo':
                processed_audio = self.apply_echo(
                    audio_data, sample_rate, 
                    delay=0.2 + intensity_normalized * 0.5,
                    wet_level=intensity_normalized * 0.6
                )
            elif effect_name.lower() == 'chorus':
                processed_audio = self.apply_chorus(
                    audio_data, sample_rate,
                    rate=1.0 + intensity_normalized * 2.0,
                    wet_level=intensity_normalized * 0.7
                )
            elif effect_name.lower() == 'distortion':
                processed_audio = self.apply_distortion(
                    audio_data,
                    gain=1.0 + intensity_normalized * 4.0,
                    wet_level=intensity_normalized
                )
            elif effect_name.lower() == 'compressor':
                processed_audio = self.apply_compressor(
                    audio_data,
                    threshold=0.8 - intensity_normalized * 0.5,
                    wet_level=intensity_normalized
                )
            elif effect_name.lower() == 'equalizer':
                # Random EQ curve based on intensity
                low_gain = 0.5 + intensity_normalized
                mid_gain = 1.0 + (intensity_normalized - 0.5) * 0.5
                high_gain = 0.7 + intensity_normalized * 0.6
                processed_audio = self.apply_equalizer(
                    audio_data, sample_rate,
                    low_gain=low_gain, mid_gain=mid_gain, high_gain=high_gain,
                    wet_level=intensity_normalized
                )
            elif effect_name.lower() == 'delay':
                # Delay is similar to echo with longer times
                processed_audio = self.apply_echo(
                    audio_data, sample_rate,
                    delay=0.5 + intensity_normalized * 1.0,
                    decay=0.3 + intensity_normalized * 0.4,
                    wet_level=intensity_normalized * 0.5
                )
            else:
                raise ValueError(f"Unknown effect: {effect_name}")
            
            # Generate output filename
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_{effect_name}_{int(intensity)}.wav"
            
            # Save processed audio
            self.save_audio(processed_audio, sample_rate, output_filename)
            
            logger.info(f"Effect {effect_name} applied successfully to {filename}")
            return output_filename
            
        except Exception as e:
            logger.error(f"Effect application error: {str(e)}")
            raise
    
    def get_audio_info(self, filename: str) -> Dict[str, Any]:
        """Get audio file information."""
        try:
            filepath = os.path.join(self.upload_folder, filename)
            
            # Load audio for analysis
            audio_data, sample_rate = self.load_audio(filename)
            
            # Calculate duration
            if len(audio_data.shape) == 1:
                duration = len(audio_data) / sample_rate
                channels = 1
            else:
                duration = len(audio_data[0]) / sample_rate
                channels = audio_data.shape[0]
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            return {
                'filename': filename,
                'duration': round(duration, 2),
                'sample_rate': sample_rate,
                'channels': channels,
                'file_size': file_size,
                'format': os.path.splitext(filename)[1].lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info for {filename}: {str(e)}")
            raise
    
    def convert_to_mp3(self, wav_filename: str, quality: str = 'high') -> str:
        """Convert WAV file to MP3."""
        try:
            wav_path = os.path.join(self.processed_folder, wav_filename)
            mp3_filename = os.path.splitext(wav_filename)[0] + '.mp3'
            mp3_path = os.path.join(self.processed_folder, mp3_filename)
            
            # Load audio with pydub
            audio = AudioSegment.from_wav(wav_path)
            
            # Set bitrate based on quality
            bitrate_map = {
                'low': '128k',
                'medium': '192k', 
                'high': '320k'
            }
            bitrate = bitrate_map.get(quality, '192k')
            
            # Export as MP3
            audio.export(mp3_path, format='mp3', bitrate=bitrate)
            
            logger.info(f"Converted {wav_filename} to MP3: {mp3_filename}")
            return mp3_filename
            
        except Exception as e:
            logger.error(f"MP3 conversion error: {str(e)}")
            raise