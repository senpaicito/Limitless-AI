"""Core plugins for AI Companion"""
from .cli_interface import CLInterfacePlugin
from .webui import WebUIPlugin
from .discord_bot import DiscordBot
from .vtube_studio import VTubeStudioPlugin
from .piper_tts import PiperTTSPlugin

__all__ = [
    'CLInterfacePlugin', 
    'WebUIPlugin', 
    'DiscordBot', 
    'VTubeStudioPlugin', 
    'PiperTTSPlugin'
]
