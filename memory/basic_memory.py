from .memory_manager import MemoryManager, Memory

class BasicMemoryManager(MemoryManager):
    """Basic in-memory storage implementation for Phase 1"""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger.info("Initialized Basic Memory Manager")
        
    def add_conversation_memory(self, user_input: str, ai_response: str, 
                              emotional_context: str = "neutral") -> str:
        """Helper method to add conversation memory"""
        memory_content = f"User: {user_input}\nAI: {ai_response}"
        memory = Memory(
            content=memory_content,
            memory_type="conversation",
            emotional_context=emotional_context,
            importance=0.7  # Conversation memories are moderately important
        )
        return self.add_memory(memory)
        
    def add_user_fact(self, fact: str, emotional_context: str = "neutral", 
                     importance: float = 0.8) -> str:
        """Helper method to add user facts"""
        memory = Memory(
            content=f"User fact: {fact}",
            memory_type="fact",
            emotional_context=emotional_context,
            importance=importance
        )
        return self.add_memory(memory)
        
    def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        """Get conversation history in message format"""
        recent_memories = self.get_recent_memories(limit)
        conversations = []
        
        for memory in recent_memories:
            if memory.memory_type == "conversation" and "User:" in memory.content:
                parts = memory.content.split("\nAI: ")
                if len(parts) == 2:
                    user_part = parts[0].replace("User: ", "")
                    conversations.append({
                        'role': 'user',
                        'content': user_part,
                        'timestamp': memory.timestamp
                    })
                    conversations.append({
                        'role': 'assistant', 
                        'content': parts[1],
                        'timestamp': memory.timestamp
                    })
                    
        return sorted(conversations, key=lambda x: x['timestamp'])[-limit*2:]
