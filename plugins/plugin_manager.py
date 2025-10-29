import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, Any, List, Type
from .plugin_base import PluginBase

class PluginManager:
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        self.config = config
        self.character_manager = character_manager
        self.memory_manager = memory_manager
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        self.plugins: Dict[str, PluginBase] = {}
        self.available_plugins: List[str] = []
        
    def load_plugins(self) -> bool:
        """Load all enabled plugins"""
        try:
            if not self.config.get('plugins.enabled', True):
                self.logger.info("Plugins are disabled in configuration")
                return True
                
            # Load core plugins
            core_plugins = self.config.get('plugins.core_plugins', [])
            for plugin_name in core_plugins:
                self.load_plugin(f"plugins.core_plugins.{plugin_name}")
                
            # Load custom plugins (Phase 2)
            custom_plugins_path = self.config.get('plugins.plugins_path', './plugins/custom_plugins')
            # Custom plugin loading logic will be implemented in Phase 2
            
            self.logger.info(f"Loaded {len(self.plugins)} plugins: {list(self.plugins.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading plugins: {e}")
            return False
            
    def load_plugin(self, plugin_module: str) -> bool:
        """Load a specific plugin by module path"""
        try:
            module = importlib.import_module(plugin_module)
            
            # Find plugin classes in module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    
                    plugin_instance = obj(
                        self.config,
                        self.character_manager,
                        self.memory_manager,
                        self.ai_engine
                    )
                    
                    if plugin_instance.initialize():
                        self.plugins[plugin_instance.get_name()] = plugin_instance
                        self.logger.info(f"Successfully loaded plugin: {plugin_instance.get_name()}")
                        return True
                    else:
                        self.logger.error(f"Failed to initialize plugin: {plugin_instance.get_name()}")
                        return False
                        
            self.logger.warning(f"No plugin class found in module: {plugin_module}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_module}: {e}")
            return False
            
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
                self.logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
                return False
        return False
        
    def get_plugin(self, plugin_name: str) -> PluginBase:
        """Get a plugin instance by name"""
        return self.plugins.get(plugin_name)
        
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.plugins.keys())
        
    def broadcast_message_received(self, message: str, message_type: str = "user") -> None:
        """Broadcast message received event to all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    plugin.on_message_received(message, message_type)
                except Exception as e:
                    self.logger.error(f"Error in plugin {plugin.get_name()} on_message_received: {e}")
                    
    def broadcast_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Broadcast message sent event to all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    plugin.on_message_sent(message, message_type)
                except Exception as e:
                    self.logger.error(f"Error in plugin {plugin.get_name()} on_message_sent: {e}")
                    
    def broadcast_memory_added(self, memory_content: str, memory_type: str) -> None:
        """Broadcast memory added event to all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    plugin.on_memory_added(memory_content, memory_type)
                except Exception as e:
                    self.logger.error(f"Error in plugin {plugin.get_name()} on_memory_added: {e}")
                    
    def cleanup_all(self) -> None:
        """Cleanup all plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)