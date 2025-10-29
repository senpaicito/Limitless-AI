from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

class PluginBase(ABC):
    """Base class for all AI Companion plugins"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        self.config = config
        self.character_manager = character_manager
        self.memory_manager = memory_manager
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(f"plugin.{self.get_name()}")
        self.enabled = True
        
    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name"""
        pass
        
    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version"""
        pass
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
        
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this plugin"""
        return {}
        
    def on_message_received(self, message: str, message_type: str = "user") -> None:
        """Called when a message is received (can be overridden)"""
        pass
        
    def on_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Called when a message is sent (can be overridden)"""
        pass
        
    def on_memory_added(self, memory_content: str, memory_type: str) -> None:
        """Called when a memory is added (can be overridden)"""
        pass
        
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the plugin"""
        self.enabled = enabled
        self.logger.info(f"Plugin {self.get_name()} {'enabled' if enabled else 'disabled'}")