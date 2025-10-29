#!/usr/bin/env python3
"""
Basic chat test for AI Companion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_engine import AIEngine

def test_basic_chat():
    """Test basic chat functionality"""
    print("🤖 Testing Basic Chat Functionality...")
    print("=" * 50)
    
    # Initialize AI Engine
    engine = AIEngine()
    if not engine.initialize():
        print("❌ Failed to initialize AI Engine")
        return False
        
    # Test messages
    test_messages = [
        "Hello!",
        "What's your name?",
        "Tell me a fun fact",
        "How are you feeling today?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[{i}/4] You: {message}")
        response = engine.process_message(message)
        print(f"🤖 {engine.character_manager.get_name()}: {response}")
        
        # Basic validation
        if not response or len(response) < 5:
            print("❌ Invalid response received")
            return False
            
    print("\n" + "=" * 50)
    print("✅ Basic chat test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_basic_chat()
    sys.exit(0 if success else 1)