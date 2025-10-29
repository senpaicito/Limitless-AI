import os
import logging
import threading
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import platform
from plugins.plugin_base import PluginBase

try:
    import piper_tts
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    piper_tts = None

class PiperTTSPlugin(PluginBase):
    """Piper TTS integration for AI Companion using Python package"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        super().__init__(config, character_manager, memory_manager, ai_engine)
        self.voice = None
        self.temp_dir = None
        self.audio_queue = []
        self.queue_lock = threading.Lock()
        self.processing_thread = None
        self.should_process = True
        
    def get_name(self) -> str:
        return "piper_tts"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> bool:
        """Initialize Piper TTS using Python package"""
        if not self.config.get('integrations.piper_tts.enabled', False):
            self.logger.info("Piper TTS integration is disabled in configuration")
            return True
            
        if not PIPER_AVAILABLE:
            self.logger.error("piper-tts Python package not available. Install with: pip install piper-tts")
            return False
            
        try:
            # Initialize Piper voice
            model_path = self.config.get('integrations.piper_tts.model_path', '')
            voice_name = self.config.get('integrations.piper_tts.voice', 'en_US-lessac-medium')
            
            if model_path and Path(model_path).exists():
                # Use specific model file
                self.voice = piper_tts.PiperVoice.load(model_path)
            else:
                # Try to download and use a voice
                self.voice = self._get_voice(voice_name)
                
            if not self.voice:
                self.logger.error(f"Could not initialize Piper voice: {voice_name}")
                return False
                
            # Create temp directory for audio files
            self.temp_dir = tempfile.mkdtemp(prefix="piper_tts_")
            
            # Start audio processing thread
            self.processing_thread = threading.Thread(target=self.process_audio_queue, daemon=True)
            self.processing_thread.start()
            
            self.logger.info(f"Piper TTS initialized with voice")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Piper TTS: {e}")
            return False
            
    def _get_voice(self, voice_name: str):
        """Get or download a Piper voice"""
        try:
            # List of available voices in the package
            available_voices = {
                'en_US-lessac-medium': 'en_US-lessac-medium',
                'en_US-lessac-low': 'en_US-lessac-low', 
                'en_GB-alan-medium': 'en_GB-alan-medium',
                'en_GB-alan-low': 'en_GB-alan-low'
            }
            
            if voice_name in available_voices:
                return piper_tts.PiperVoice.load(available_voices[voice_name])
            else:
                # Try to use the voice name directly
                return piper_tts.PiperVoice.load(voice_name)
                
        except Exception as e:
            self.logger.error(f"Error getting voice {voice_name}: {e}")
            return None
            
    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """Convert text to speech using Piper Python package"""
        if not self.voice:
            return None
            
        if not output_file:
            output_file = Path(self.temp_dir) / f"tts_{hash(text) % 10000}.wav"
            
        try:
            # Generate speech using Piper
            audio_data = self.voice.synthesize(text)
            
            # Save to file
            with open(output_file, 'wb') as f:
                f.write(audio_data)
                
            self.logger.debug(f"Generated TTS audio: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Piper TTS synthesis error: {e}")
            return None
            
    def speak_text(self, text: str) -> bool:
        """Speak text immediately using Piper"""
        try:
            audio_file = self.text_to_speech(text)
            if audio_file:
                return self.play_audio(audio_file)
            return False
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            return False
            
    def play_audio(self, audio_file: str) -> bool:
        """Play audio file using system audio player"""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Use Windows Media Player
                subprocess.Popen(["cmd", "/c", "start", "/min", "", audio_file], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["afplay", audio_file])
            else:  # Linux
                # Try multiple audio players
                players = ["aplay", "paplay", "play"]
                for player in players:
                    try:
                        subprocess.Popen([player, audio_file])
                        return True
                    except FileNotFoundError:
                        continue
                self.logger.error("No audio player found on Linux")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            return False
            
    def queue_speech(self, text: str):
        """Add text to speech queue"""
        with self.queue_lock:
            self.audio_queue.append(text)
            
    def process_audio_queue(self):
        """Process audio queue in background thread"""
        while self.should_process:
            with self.queue_lock:
                if self.audio_queue:
                    text = self.audio_queue.pop(0)
                else:
                    text = None
                    
            if text:
                try:
                    self.speak_text(text)
                except Exception as e:
                    self.logger.error(f"Error processing TTS queue: {e}")
                    
            threading.Event().wait(0.1)  # Small delay
            
    def on_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Convert AI responses to speech"""
        if not self.enabled or message_type != "ai":
            return
            
        # Don't speak very short messages or commands
        if len(message.strip()) < 5:
            return
            
        # Check if TTS is enabled for responses
        if not self.config.get('integrations.piper_tts.speak_responses', True):
            return
            
        # Queue the message for TTS
        self.queue_speech(message)
        
    def get_voice_info(self) -> Dict[str, Any]:
        """Get information about the current voice"""
        if not self.voice:
            return {}
            
        return {
            'name': getattr(self.voice, 'name', 'Unknown'),
            'language': getattr(self.voice, 'language', 'Unknown'),
            'sample_rate': getattr(self.voice, 'sample_rate', 0),
            'available': True
        }
        
    def cleanup(self):
        """Cleanup Piper TTS resources"""
        self.should_process = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
            
        # Cleanup temp directory
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(f"Error cleaning up temp directory: {e}")
                
        self.logger.info("Piper TTS plugin cleaned up")
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'integrations.piper_tts.enabled': {
                'type': 'boolean',
                'default': False,
                'description': 'Enable Piper TTS integration'
            },
            'integrations.piper_tts.model_path': {
                'type': 'string',
                'default': '',
                'description': 'Path to Piper voice model (optional, uses package voices by default)'
            },
            'integrations.piper_tts.voice': {
                'type': 'string',
                'default': 'en_US-lessac-medium',
                'description': 'Voice to use (en_US-lessac-medium, en_GB-alan-medium, etc.)'
            },
            'integrations.piper_tts.speak_responses': {
                'type': 'boolean',
                'default': True,
                'description': 'Speak AI responses automatically'
            }
        }