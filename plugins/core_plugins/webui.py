import logging
import threading
from plugins.plugin_base import PluginBase

class WebUIPlugin(PluginBase):
    """Plugin for WebUI functionality"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        super().__init__(config, character_manager, memory_manager, ai_engine)
        self.webui = None
        self.webui_thread = None
        
    def get_name(self) -> str:
        return "webui"
        
    def get_version(self) -> str:
        return "2.0.0"
        
    def initialize(self) -> bool:
        """Initialize WebUI"""
        if not self.config.get('webui.enabled', True):
            self.logger.info("WebUI is disabled in configuration")
            return True
            
        try:
            from webui.app import WebUI
            self.webui = WebUI(
                self.config,
                self.character_manager,
                self.memory_manager,
                self.ai_engine
            )
            
            # Start WebUI in a separate thread
            self.webui_thread = threading.Thread(target=self.webui.start, daemon=True)
            self.webui_thread.start()
            
            self.logger.info("WebUI plugin initialized and started")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize WebUI plugin: %s", e)
            return False
            
    def cleanup(self) -> None:
        """Cleanup WebUI"""
        if self.webui:
            self.webui.stop()
        self.logger.info("WebUI plugin cleaned up")
        
    def get_config_schema(self) -> dict:
        return {
            'webui.enabled': {
                'type': 'boolean',
                'default': True,
                'description': 'Enable the WebUI interface'
            },
            'webui.host': {
                'type': 'string', 
                'default': '127.0.0.1',
                'description': 'WebUI server host'
            },
            'webui.port': {
                'type': 'integer',
                'default': 5000,
                'description': 'WebUI server port'
            }
        }
        
    def on_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Handle AI responses - ensure they're processed by WebUI"""
        if message_type == "ai":
            self.logger.debug("AI response processed by WebUI plugin")