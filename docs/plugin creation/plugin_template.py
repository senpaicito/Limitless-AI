from plugins.plugin_base import PluginBase
import logging
from typing import Dict, Any

class YourPluginName(PluginBase):
    def get_name(self) -> str:
        return "your_plugin_name"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> bool:
        # Your initialization code
        return True
        
    def cleanup(self) -> None:
        # Your cleanup code
        pass
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'your.plugin.setting': {
                'type': 'boolean',
                'default': False,
                'description': 'Your setting description'
            }
        }