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
            self.logger.info("Loading core plugins: %s", core_plugins)
            
            for plugin_name in core_plugins:
                self.logger.info("Attempting to load plugin: %s", plugin_name)
                
                # Try different naming conventions
                module_paths = [
                    f"plugins.core_plugins.{plugin_name}",
                    f"plugins.core_plugins.{plugin_name}_plugin", 
                    f"plugins.core_plugins.{plugin_name.replace('_plugin', '')}",
                    plugin_name  # Direct import
                ]
                
                loaded = False
                last_error = None
                
                for module_path in module_paths:
                    try:
                        if self.load_plugin(module_path):
                            loaded = True
                            self.logger.info("Successfully loaded plugin: %s from %s", plugin_name, module_path)
                            break
                        else:
                            self.logger.debug("Failed to load %s from %s", plugin_name, module_path)
                    except Exception as e:
                        last_error = e
                        self.logger.debug("Error loading %s from %s: %s", plugin_name, module_path, e)
                
                if not loaded:
                    self.logger.warning("Could not load core plugin: %s. Last error: %s", plugin_name, last_error)
                
            # Load custom plugins
            custom_plugins_path = self.config.get('plugins.plugins_path', './plugins/custom_plugins')
            if Path(custom_plugins_path).exists():
                self.load_custom_plugins(custom_plugins_path)
            
            # Final status report
            loaded_plugins = self.get_loaded_plugins()
            self.logger.info("Loaded %d plugins: %s", len(loaded_plugins), loaded_plugins)
                
            return True
            
        except Exception as e:
            self.logger.error("Error loading plugins: %s", e)
            return False
            
    def load_plugin(self, plugin_module: str) -> bool:
        """Load a specific plugin by module path with enhanced error handling"""
        try:
            self.logger.debug("Loading plugin module: %s", plugin_module)
            
            # Handle direct class names
            if plugin_module in ['discord_bot', 'vtube_studio', 'piper_tts']:
                plugin_module = f"plugins.core_plugins.{plugin_module}"
            
            module = importlib.import_module(plugin_module)
            self.logger.debug("Imported module: %s", plugin_module)
            
            # Find plugin classes in module
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin_classes.append((name, obj))
                    self.logger.debug("Found plugin class: %s", name)
            
            if not plugin_classes:
                self.logger.warning("No plugin classes found in module: %s", plugin_module)
                return False
                
            for class_name, plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class(
                        self.config,
                        self.character_manager,
                        self.memory_manager,
                        self.ai_engine
                    )
                    
                    self.logger.debug("Initializing plugin: %s", plugin_instance.get_name())
                    
                    if plugin_instance.initialize():
                        self.plugins[plugin_instance.get_name()] = plugin_instance
                        self.logger.info("Successfully initialized plugin: %s v%s", plugin_instance.get_name(), plugin_instance.get_version())
                        return True
                    else:
                        self.logger.error("Failed to initialize plugin: %s", plugin_instance.get_name())
                        return False
                        
                except Exception as e:
                    self.logger.error("Error creating plugin instance %s: %s", class_name, e)
                    continue
                        
            self.logger.warning("No valid plugin classes could be initialized in: %s", plugin_module)
            return False
            
        except ImportError as e:
            self.logger.debug("Module not found: %s - %s", plugin_module, e)
            return False
        except Exception as e:
            self.logger.error("Error loading plugin %s: %s", plugin_module, e)
            return False
            
    def load_custom_plugins(self, plugins_path: str) -> None:
        """Load custom plugins from directory"""
        try:
            plugins_dir = Path(plugins_path)
            if not plugins_dir.exists():
                self.logger.info("Custom plugins directory not found: %s", plugins_path)
                return
                
            self.logger.info("Scanning for custom plugins in: %s", plugins_path)
            
            # Add plugins path to Python path
            import sys
            if str(plugins_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugins_dir.parent))
            
            plugin_files = list(plugins_dir.glob("*.py"))
            self.logger.info("Found %d potential plugin files", len(plugin_files))
            
            for plugin_file in plugin_files:
                if plugin_file.name.startswith("_"):
                    continue
                    
                module_name = plugin_file.stem
                self.logger.info("Attempting to load custom plugin: %s", module_name)
                
                try:
                    # Try to load as custom plugin
                    module = importlib.import_module(f"plugins.custom_plugins.{module_name}")
                    
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
                                self.logger.info("Loaded custom plugin: %s", plugin_instance.get_name())
                            else:
                                self.logger.error("Failed to initialize custom plugin: %s", plugin_instance.get_name())
                            
                except Exception as e:
                    self.logger.error("Error loading custom plugin %s: %s", module_name, e)
                    
        except Exception as e:
            self.logger.error("Error loading custom plugins: %s", e)
            
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name in self.plugins:
            try:
                self.logger.info("Unloading plugin: %s", plugin_name)
                self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
                self.logger.info("Unloaded plugin: %s", plugin_name)
                return True
            except Exception as e:
                self.logger.error("Error unloading plugin %s: %s", plugin_name, e)
                return False
        else:
            self.logger.warning("Plugin not found for unloading: %s", plugin_name)
            return False
        
    def get_plugin(self, plugin_name: str) -> PluginBase:
        """Get a plugin instance by name"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            self.logger.debug("Plugin not found: %s", plugin_name)
        return plugin
        
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.plugins.keys())
        
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all plugins"""
        status = {}
        for name, plugin in self.plugins.items():
            status[name] = {
                'name': plugin.get_name(),
                'version': plugin.get_version(),
                'enabled': plugin.is_enabled(),
                'initialized': True
            }
        return status
        
    def broadcast_message_received(self, message: str, message_type: str = "user") -> None:
        """Broadcast message received event to all plugins"""
        for plugin_name, plugin in self.plugins.items():
            if plugin.is_enabled():
                try:
                    plugin.on_message_received(message, message_type)
                    self.logger.debug("Message received broadcast to: %s", plugin_name)
                except Exception as e:
                    self.logger.error("Error in plugin %s on_message_received: %s", plugin_name, e)
                    
    def broadcast_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Broadcast message sent event to all plugins"""
        for plugin_name, plugin in self.plugins.items():
            if plugin.is_enabled():
                try:
                    plugin.on_message_sent(message, message_type)
                    self.logger.debug("Message sent broadcast to: %s", plugin_name)
                except Exception as e:
                    self.logger.error("Error in plugin %s on_message_sent: %s", plugin_name, e)
                    
    def broadcast_memory_added(self, memory_content: str, memory_type: str) -> None:
        """Broadcast memory added event to all plugins"""
        for plugin_name, plugin in self.plugins.items():
            if plugin.is_enabled():
                try:
                    plugin.on_memory_added(memory_content, memory_type)
                    self.logger.debug("Memory added broadcast to: %s", plugin_name)
                except Exception as e:
                    self.logger.error("Error in plugin %s on_memory_added: %s", plugin_name, e)
                    
    def cleanup_all(self) -> None:
        """Cleanup all plugins"""
        self.logger.info("Cleaning up all plugins...")
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
        self.logger.info("All plugins cleaned up")