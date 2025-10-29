import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class CharacterManager:
    def __init__(self, character_path: str = "character/default_character.yaml"):
        self.character_path = Path(character_path)
        self.character_data = {}
        self.logger = logging.getLogger(__name__)
        self.load_character()

    def load_character(self) -> Dict[str, Any]:
        """Load character configuration from YAML file"""
        try:
            if self.character_path.exists():
                with open(self.character_path, 'r', encoding='utf-8') as f:
                    self.character_data = yaml.safe_load(f)
                self.logger.info(f"Character loaded from {self.character_path}")
            else:
                self.logger.error(f"Character file not found at {self.character_path}")
                self.character_data = self.get_default_character()
        except Exception as e:
            self.logger.error(f"Error loading character: {e}")
            self.character_data = self.get_default_character()
        
        return self.character_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get character value using dot notation"""
        keys = key.split('.')
        value = self.character_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value

    def get_name(self) -> str:
        """Get character name"""
        return self.get('character.name', 'AI Companion')

    def get_personality(self) -> str:
        """Get character personality description"""
        return self.get('character.personality', '')

    def get_traits(self) -> list:
        """Get character traits"""
        return self.get('character.traits', [])

    def get_system_prompt(self, emotional_context: str = "") -> str:
        """Generate system prompt with dynamic values"""
        base_prompt = self.get('character.system_prompt', '')
        
        replacements = {
            '{name}': self.get_name(),
            '{personality}': self.get_personality(),
            '{traits}': ', '.join(self.get_traits()),
            '{behavior}': self.get('character.behavior', ''),
            '{emotional_context}': emotional_context or "neutral"
        }
        
        system_prompt = base_prompt
        for placeholder, value in replacements.items():
            system_prompt = system_prompt.replace(placeholder, value)
            
        return system_prompt

    def get_emotional_state(self) -> Dict[str, float]:
        """Get base emotional state (for Phase 2)"""
        return self.get('character.emotions.emotional_range', {})

    def save_character(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Save character configuration to file"""
        try:
            if data:
                self.character_data = data
                
            self.character_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.character_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.character_data, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"Character saved to {self.character_path}")
        except Exception as e:
            self.logger.error(f"Error saving character: {e}")

    def get_default_character(self) -> Dict[str, Any]:
        """Return default character configuration"""
        return {
            'character': {
                'name': 'Luna',
                'version': '1.0',
                'personality': 'A curious and empathetic AI companion.',
                'traits': ['curious', 'empathetic', 'supportive'],
                'behavior': 'Be supportive and understanding.',
                'system_prompt': 'You are {name}. {personality}'
            }
        }

    def validate_character(self) -> bool:
        """Validate character configuration"""
        required_fields = ['name', 'personality', 'traits']
        character_section = self.character_data.get('character', {})
        
        for field in required_fields:
            if field not in character_section:
                self.logger.error(f"Missing required character field: {field}")
                return False
        return True