"""
Lions Flute Demo Audio Generator
Creates demo audio files for testing the application
"""

import numpy as np
import soundfile as sf
import os
from scipy import signal
import math

def generate_demo_track(filename="demo_track.wav", duration=30, sample_rate=44100):
    """Generate a demo audio track with vocals and instruments."""
    
    # Time array
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    
    # Create instrumental track (combination of different instruments)
    # Bass line (low frequency)
    bass = 0.3 * np.sin(2 * np.pi * 80 * t) + 0.2 * np.sin(2 * np.pi * 120 * t)
    
    # Rhythm guitar (mid frequencies)
    guitar_freq = 220  # A3
    guitar = 0.4 * np.sin(2 * np.pi * guitar_freq * t) * (1 + 0.1 * np.sin(2 * np.pi * 4 * t))
    
    # Lead melody (higher frequencies)
    melody_freqs = [440, 523, 659, 784, 659, 523, 440]  # A4, C5, E5, G5, E5, C5, A4
    melody = np.zeros_like(t)
    note_duration = duration / len(melody_freqs)
    
    for i, freq in enumerate(melody_freqs):
        start_idx = int(i * note_duration * sample_rate)
        end_idx = int((i + 1) * note_duration * sample_rate)
        if end_idx > len(melody):
            end_idx = len(melody)
        melody[start_idx:end_idx] = 0.3 * np.sin(2 * np.pi * freq * t[start_idx:end_idx])
    
    # Add some drums (percussive elements)
    drum_beat = np.zeros_like(t)
    beat_interval = sample_rate // 2  # 2 beats per second
    for i in range(0, len(t), beat_interval):
        if i + 1000 < len(t):
            # Kick drum (low frequency burst)
            drum_beat[i:i+1000] = 0.5 * np.exp(-np.arange(1000) / 200) * np.sin(2 * np.pi * 60 * np.arange(1000) / sample_rate)
    
    # Combine instrumental elements
    instrumental = bass + guitar + melody + drum_beat
    
    # Create vocal track (more focused in mid frequencies)
    vocal_freqs = [330, 370, 415, 466, 415, 370, 330]  # Vocal melody
    vocals = np.zeros_like(t)
    
    for i, freq in enumerate(vocal_freqs):
        start_idx = int(i * note_duration * sample_rate)
        end_idx = int((i + 1) * note_duration * sample_rate)
        if end_idx > len(vocals):
            end_idx = len(vocals)
        
        # Add harmonics to make it more voice-like
        fundamental = 0.4 * np.sin(2 * np.pi * freq * t[start_idx:end_idx])
        harmonic2 = 0.2 * np.sin(2 * np.pi * freq * 2 * t[start_idx:end_idx])
        harmonic3 = 0.1 * np.sin(2 * np.pi * freq * 3 * t[start_idx:end_idx])
        
        vocals[start_idx:end_idx] = fundamental + harmonic2 + harmonic3
    
    # Add some vibrato to vocals
    vibrato = 1 + 0.05 * np.sin(2 * np.pi * 5 * t)  # 5 Hz vibrato
    vocals = vocals * vibrato
    
    # Combine vocals and instrumental
    mixed_audio = 0.7 * instrumental + 0.8 * vocals
    
    # Normalize to prevent clipping
    mixed_audio = mixed_audio / np.max(np.abs(mixed_audio)) * 0.8
    
    # Save as stereo (duplicate mono to both channels)
    stereo_audio = np.column_stack((mixed_audio, mixed_audio))
    
    # Ensure uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    sf.write(filepath, stereo_audio, sample_rate)
    
    print(f"Generated demo track: {filepath}")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Channels: 2 (stereo)")
    
    return filepath

def generate_multiple_demos():
    """Generate multiple demo files for testing."""
    
    # Short demo (10 seconds)
    generate_demo_track("demo_short.wav", duration=10)
    
    # Medium demo (30 seconds) 
    generate_demo_track("demo_medium.wav", duration=30)
    
    # Different style - electronic
    generate_electronic_demo("demo_electronic.wav", duration=20)

def generate_electronic_demo(filename="demo_electronic.wav", duration=20, sample_rate=44100):
    """Generate an electronic music demo."""
    
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    
    # Electronic bass (sawtooth wave)
    bass_freq = 55  # A1
    bass = 0.4 * signal.sawtooth(2 * np.pi * bass_freq * t)
    
    # Synthesizer pad (multiple sine waves with slight detuning)
    pad = np.zeros_like(t)
    chord_freqs = [220, 277, 330]  # A minor chord
    for freq in chord_freqs:
        pad += 0.2 * np.sin(2 * np.pi * freq * t)
        pad += 0.1 * np.sin(2 * np.pi * (freq * 1.01) * t)  # Slight detune
    
    # Electronic lead (square wave with filter sweep)
    lead_freq = 440
    lead = 0.3 * signal.square(2 * np.pi * lead_freq * t)
    
    # Add filter sweep effect
    cutoff_freq = 1000 + 500 * np.sin(2 * np.pi * 0.5 * t)
    for i in range(len(lead)):
        if i > 0:
            # Simple low-pass filter
            alpha = 2 * np.pi * cutoff_freq[i] / sample_rate
            if alpha > 1:
                alpha = 1
            lead[i] = alpha * lead[i] + (1 - alpha) * lead[i-1]
    
    # Electronic drums
    drums = np.zeros_like(t)
    beat_interval = sample_rate // 4  # 4 beats per second
    for i in range(0, len(t), beat_interval):
        if i + 500 < len(t):
            # Electronic kick
            drums[i:i+500] = 0.6 * np.exp(-np.arange(500) / 100) * np.sin(2 * np.pi * 80 * np.arange(500) / sample_rate)
        
        # Hi-hat on off-beats
        if i + beat_interval//2 + 100 < len(t):
            hihat_start = i + beat_interval//2
            drums[hihat_start:hihat_start+100] = 0.3 * np.random.normal(0, 1, 100) * np.exp(-np.arange(100) / 20)
    
    # Combine all elements
    electronic_mix = bass + pad + lead + drums
    
    # Add some reverb-like effect
    reverb_delay = int(0.1 * sample_rate)  # 100ms delay
    reverb_audio = np.zeros_like(electronic_mix)
    reverb_audio[reverb_delay:] = electronic_mix[:-reverb_delay] * 0.3
    electronic_mix = electronic_mix + reverb_audio
    
    # Normalize
    electronic_mix = electronic_mix / np.max(np.abs(electronic_mix)) * 0.8
    
    # Convert to stereo
    stereo_audio = np.column_stack((electronic_mix, electronic_mix))
    
    # Ensure uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    sf.write(filepath, stereo_audio, sample_rate)
    
    print(f"Generated electronic demo: {filepath}")
    return filepath

if __name__ == "__main__":
    print("Generating demo audio files...")
    generate_multiple_demos()
    print("Demo generation complete!")