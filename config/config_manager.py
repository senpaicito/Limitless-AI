import json
import os
import logging
from typing import Any, Dict
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path: str = "config/default_config.json"):
        self.config_path = Path(config_path)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Config file not found at {self.config_path}, using defaults")
                self.config = self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = self.get_default_config()
        
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config_ref = self.config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
            
        config_ref[keys[-1]] = value
        self.save_config()

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "core": {"name": "AI Companion", "version": "1.0.0", "debug": True},
            "ollama": {"model": "llama2", "base_url": "http://localhost:11434", "temperature": 0.7, "max_tokens": 500},
            "memory": {"type": "basic", "max_memories": 1000, "semantic_search_enabled": False},
            "webui": {"enabled": False, "host": "127.0.0.1", "port": 5000, "debug": False},
            "plugins": {"enabled": True, "plugins_path": "./plugins/custom_plugins", "core_plugins": ["cli_interface"]},
            "integrations": {
                "discord": {"enabled": False, "token": "", "channel_id": ""},
                "vtube_studio": {"enabled": False, "websocket_url": "ws://localhost:8001"},
                "piper_tts": {"enabled": False, "model_path": "", "voice": "en_US-lessac-medium"}
            },
            "personality": {"learning_enabled": True, "adaptation_rate": 0.1, "emotional_context": True}
        }

    def validate_config(self) -> bool:
        """Validate the current configuration"""
        required_sections = ['core', 'ollama', 'memory', 'plugins']
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Missing required config section: {section}")
                return False
        return True