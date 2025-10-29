#!/usr/bin/env python3
"""
Memory system test for AI Companion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.config_manager import ConfigManager
from memory.basic_memory import BasicMemoryManager

def test_memory_system():
    """Test memory system functionality"""
    print("🧠 Testing Memory System...")
    print("=" * 50)
    
    # Initialize components
    config = ConfigManager()
    memory_manager = BasicMemoryManager(config)
    
    # Test adding memories
    test_memories = [
        ("I love programming and AI", "fact", "excited"),
        ("My favorite color is blue", "fact", "happy"),
        ("User: What's your name?\nAI: I'm Luna!", "conversation", "neutral")
    ]
    
    for content, mem_type, emotion in test_memories:
        memory_id = memory_manager.add_conversation_memory(
            f"Test: {content}", f"Test response to {content}", emotion
        )
        if memory_id:
            print(f"✓ Memory added: {content[:30]}...")
        else:
            print(f"❌ Failed to add memory: {content[:30]}...")
            return False
    
    # Test retrieving memories
    recent_memories = memory_manager.get_recent_memories(5)
    print(f"✓ Retrieved {len(recent_memories)} recent memories")
    
    # Test memory search
    search_results = memory_manager.search_memories("programming", 3)
    print(f"✓ Found {len(search_results)} memories for 'programming'")
    
    # Test memory stats
    stats = memory_manager.get_memory_stats()
    print(f"✓ Memory stats: {stats['total_memories']} total memories")
    
    print("\n" + "=" * 50)
    print("✅ Memory system test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_memory_system()
    sys.exit(0 if success else 1)