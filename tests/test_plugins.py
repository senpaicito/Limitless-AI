#!/usr/bin/env python3
"""
Plugin system test for AI Companion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.config_manager import ConfigManager
from character.character_manager import CharacterManager
from memory.basic_memory import BasicMemoryManager
from plugins.plugin_manager import PluginManager
from ai_engine import AIEngine

def test_plugin_system():
    """Test plugin system functionality"""
    print("🔌 Testing Plugin System...")
    print("=" * 50)
    
    # Initialize core components
    config = ConfigManager()
    character_manager = CharacterManager()
    memory_manager = BasicMemoryManager(config)
    ai_engine = AIEngine()
    
    # Initialize plugin manager
    plugin_manager = PluginManager(
        config, character_manager, memory_manager, ai_engine
    )
    
    # Test plugin loading
    if not plugin_manager.load_plugins():
        print("❌ Failed to load plugins")
        return False
        
    # Check loaded plugins
    loaded_plugins = plugin_manager.get_loaded_plugins()
    print(f"✓ Loaded plugins: {loaded_plugins}")
    
    if "cli_interface" not in loaded_plugins:
        print("❌ CLI interface plugin not loaded")
        return False
        
    # Test plugin functionality
    cli_plugin = plugin_manager.get_plugin("cli_interface")
    if not cli_plugin:
        print("❌ Could not get CLI plugin instance")
        return False
        
    print(f"✓ CLI plugin: {cli_plugin.get_name()} v{cli_plugin.get_version()}")
    print(f"✓ Plugin enabled: {cli_plugin.is_enabled()}")
    
    # Test plugin events
    try:
        plugin_manager.broadcast_message_received("Test message", "user")
        plugin_manager.broadcast_message_sent("Test response", "ai")
        print("✓ Plugin event broadcasting working")
    except Exception as e:
        print(f"❌ Plugin event error: {e}")
        return False
    
    # Cleanup
    plugin_manager.cleanup_all()
    
    print("\n" + "=" * 50)
    print("✅ Plugin system test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_plugin_system()
    sys.exit(0 if success else 1)