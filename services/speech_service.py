"""
Speech Service
Handles speech-to-text and text-to-speech functionality
"""

import os
import wave
import tempfile
import json
import requests
import threading
import numpy as np
import pyaudio
from datetime import datetime
from faster_whisper import WhisperModel
from config.settings import AUDIO_SETTINGS, WHISPER_SETTINGS, TTS_SETTINGS

class SpeechService:
    """Service for speech recognition and synthesis"""
    
    def __init__(self):
        self.recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.silence_threshold = AUDIO_SETTINGS["silence_threshold"]
        self.silence_duration = AUDIO_SETTINGS["silence_duration"]
        
        # Initialize whisper model
        try:
            model_size = WHISPER_SETTINGS["model_size"]
            device = WHISPER_SETTINGS["device"]
            model_path = WHISPER_SETTINGS["model_path"]
            
            # Only load model if the path exists
            if os.path.exists(model_path):
                self.whisper_model = WhisperModel(model_size, device=device, download_root=model_path)
            else:
                # Otherwise, use the default path
                self.whisper_model = WhisperModel(model_size, device=device)
                
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.whisper_model = None
        
        # Load TTS API key
        self.tts_api_key = self._load_tts_api_key()
    
    def _load_tts_api_key(self):
        """Load Elevenlabs API key from file"""
        api_key_file = TTS_SETTINGS["api_key_file"]
        
        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r') as f:
                    data = json.load(f)
                    return data.get("elevenlabs_api_key", "")
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # If we can't load from file, try environment variable
        return os.environ.get("ELEVENLABS_API_KEY", "")
    
    def record_and_transcribe(self):
        """
        Record audio and transcribe to text
        
        Returns:
            str: Transcribed text
        """
        # Start recording
        self.start_recording()
        
        # Continue recording until silence is detected
        self.wait_for_silence()
        
        # Stop recording
        self.stop_recording()
        
        # Transcribe the recorded audio
        return self.transcribe_audio()
    
    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.frames = []
        
        # Configure audio stream
        self.stream = self.audio.open(
            format=AUDIO_SETTINGS["format"],
            channels=AUDIO_SETTINGS["channels"],
            rate=AUDIO_SETTINGS["rate"],
            input=True,
            frames_per_buffer=AUDIO_SETTINGS["chunk"],
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
    
    def stop_recording(self):
        """Stop recording audio"""
        if self.stream and self.recording:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def wait_for_silence(self):
        """Wait until silence is detected to stop recording"""
        consecutive_silence = 0
        samples_per_check = int(AUDIO_SETTINGS["rate"] / AUDIO_SETTINGS["chunk"] * 0.1)  # Check every 100ms
        silence_limit = int(self.silence_duration * AUDIO_SETTINGS["rate"] / AUDIO_SETTINGS["chunk"])
        
        # We need some minimum audio
        min_audio_length = int(1.0 * AUDIO_SETTINGS["rate"] / AUDIO_SETTINGS["chunk"])
        
        while self.recording:
            # Wait until we have enough frames to check
            if len(self.frames) < samples_per_check:
                import time
                time.sleep(0.1)
                continue
                
            # Check if we have minimum audio
            if len(self.frames) < min_audio_length:
                import time
                time.sleep(0.1)
                continue
            
            # Check last 100ms of audio for silence
            audio_data = np.frombuffer(b''.join(self.frames[-samples_per_check:]), dtype=np.int16)
            
            # Calculate volume
            volume = np.abs(audio_data).mean()
            
            # Check if below silence threshold
            if volume < self.silence_threshold:
                consecutive_silence += 1
                if consecutive_silence >= silence_limit:
                    # Silence detected for the required duration
                    break
            else:
                consecutive_silence = 0
            
            # Sleep a bit before next check
            import time
            time.sleep(0.1)
    
    def transcribe_audio(self):
        """
        Transcribe recorded audio using Whisper
        
        Returns:
            str: Transcribed text
        """
        if not self.frames:
            return ""
        
        # Save recorded audio to a temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_filename = temp_file.name
        temp_file.close()
        
        try:
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(AUDIO_SETTINGS["channels"])
                wf.setsampwidth(self.audio.get_sample_size(AUDIO_SETTINGS["format"]))
                wf.setframerate(AUDIO_SETTINGS["rate"])
                wf.writeframes(b''.join(self.frames))
            
            # Transcribe with WhisperModel if available
            if self.whisper_model:
                segments, _ = self.whisper_model.transcribe(temp_filename, beam_size=5)
                transcription = " ".join([segment.text for segment in segments])
                return transcription.strip()
            else:
                return "Speech recognition model not loaded properly."
                
        except Exception as e:
            return f"Error transcribing audio: {str(e)}"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def speak_text(self, text):
        """
        Convert text to speech using Elevenlabs API
        
        Args:
            text (str): Text to convert to speech
        """
        if not text or not self.tts_api_key:
            return
        
        # Only speak meaningful chunks of text to reduce API calls
        if len(text.strip()) < 5:  # Skip very short chunks
            return
            
        # Use a single background thread and cancel previous requests
        if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
            # A thread is already running - skip this chunk to avoid overlap
            return
            
        # Start a new thread
        self.tts_thread = threading.Thread(
            target=self._speak_text_thread,
            args=(text,),
            daemon=True
        )
        self.tts_thread.start()
    
    def _speak_text_thread(self, text):
        """Background thread for text-to-speech processing"""
        try:
            voice_id = TTS_SETTINGS["voice_id"]
            
            # API endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
            
            # Request headers
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.tts_api_key
            }
            
            # Request body
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            # Make the API request
            response = requests.post(url, json=data, headers=headers, stream=True)
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_filename = temp_file.name
                
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file.close()
                
                # Play audio (platform dependent)
                self._play_audio(temp_filename)
                
                # Clean up
                os.unlink(temp_filename)
            else:
                print(f"TTS API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
    
    def _play_audio(self, audio_file):
        """
        Play audio file (platform dependent)
        
        Args:
            audio_file (str): Path to audio file
        """
        try:
            import platform
            import subprocess
            
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(audio_file)
            elif system == 'Darwin':  # macOS
                subprocess.call(['afplay', audio_file])
            else:  # Linux
                # Try mpg123 first, fall back to other players
                players = ['mpg123', 'mpg321', 'mplayer', 'cvlc']
                
                for player in players:
                    try:
                        subprocess.call([player, audio_file])
                        break
                    except FileNotFoundError:
                        continue
        
        except Exception as e:
            print(f"Error playing audio: {str(e)}")