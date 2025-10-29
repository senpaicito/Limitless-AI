import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

class Memory:
    def __init__(self, content: str, memory_type: str = "conversation", 
                 emotional_context: str = "", importance: float = 0.5,
                 metadata: Dict[str, Any] = None):
        self.content = content
        self.memory_type = memory_type
        self.emotional_context = emotional_context
        self.importance = importance  # 0.0 to 1.0
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
        self.tags = self._generate_tags()
        
    def _generate_tags(self) -> List[str]:
        """Generate basic tags from content"""
        base_tags = [self.memory_type, self.emotional_context]
        # Simple keyword extraction
        words = self.content.lower().split()
        key_words = [word for word in words if len(word) > 4][:5]
        base_tags.extend(key_words)
        return [tag for tag in base_tags if tag]
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'type': self.memory_type,
            'emotional_context': self.emotional_context,
            'importance': self.importance,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags
        }

class BaseMemoryManager(ABC):
    @abstractmethod
    def add_memory(self, memory: Memory) -> str:
        pass
        
    @abstractmethod
    def get_recent_memories(self, limit: int = 10) -> List[Memory]:
        pass
        
    @abstractmethod
    def search_memories(self, query: str, limit: int = 5) -> List[Memory]:
        pass

class MemoryManager(BaseMemoryManager):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.memories: List[Memory] = []
        self.max_memories = config.get('memory.max_memories', 1000)
        
        # Initialize vector memory if enabled
        self.vector_memory = None
        if config.get('memory.semantic_search_enabled', False):
            try:
                from .vector_db import VectorMemory
                self.vector_memory = VectorMemory(
                    config.get('memory.vector_db_path', './data/memories')
                )
                self.logger.info("Vector memory initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize vector memory: {e}")
        
    def add_memory(self, memory: Memory) -> str:
        """Add a memory to storage"""
        try:
            # Check if we need to remove old memories
            if len(self.memories) >= self.max_memories:
                # Remove least important memories first
                self.memories.sort(key=lambda x: x.importance)
                self.memories = self.memories[-self.max_memories + 1:]
                
            self.memories.append(memory)
            memory_id = f"memory_{len(self.memories)}"
            
            # Also add to vector memory if available
            if self.vector_memory:
                self.vector_memory.add_memory(
                    content=memory.content,
                    memory_type=memory.memory_type,
                    emotional_context=memory.emotional_context,
                    importance=memory.importance,
                    metadata=memory.metadata
                )
            
            self.logger.debug(f"Added memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding memory: {e}")
            return ""
            
    def get_recent_memories(self, limit: int = 10) -> List[Memory]:
        """Get most recent memories"""
        recent = sorted(self.memories, key=lambda x: x.timestamp, reverse=True)[:limit]
        return recent
        
    def search_memories(self, query: str, limit: int = 5, use_semantic: bool = True) -> List[Memory]:
        """Search through memories with optional semantic search"""
        if use_semantic and self.vector_memory:
            return self._semantic_search(query, limit)
        else:
            return self._basic_search(query, limit)
            
    def _basic_search(self, query: str, limit: int = 5) -> List[Memory]:
        """Basic search through memories"""
        query_lower = query.lower()
        matches = []
        
        for memory in self.memories:
            # Simple content matching
            if (query_lower in memory.content.lower() or 
                any(query_lower in tag for tag in memory.tags)):
                matches.append(memory)
                
        # Sort by relevance (simple implementation)
        matches.sort(key=lambda x: (
            query_lower in x.content.lower(),
            x.importance,
            x.timestamp
        ), reverse=True)
        
        return matches[:limit]
        
    def _semantic_search(self, query: str, limit: int = 5) -> List[Memory]:
        """Semantic search using vector memory"""
        if not self.vector_memory:
            return self._basic_search(query, limit)
            
        vector_results = self.vector_memory.semantic_search(query, limit * 2)
        
        # Convert back to Memory objects
        memories = []
        for result in vector_results:
            memory = Memory(
                content=result['content'],
                memory_type=result['type'],
                emotional_context=result['emotional_context'],
                importance=result['importance'],
                metadata=result.get('metadata', {})
            )
            memory.timestamp = datetime.fromisoformat(result['timestamp'])
            memories.append(memory)
            
        return memories[:limit]
        
    def semantic_search(self, query: str, limit: int = 5) -> List[Memory]:
        """Explicit semantic search"""
        return self.search_memories(query, limit, use_semantic=True)
        
    def search_by_emotion(self, emotion: str, limit: int = 10) -> List[Memory]:
        """Search memories by emotional context"""
        emotion_memories = []
        
        for memory in self.memories:
            if emotion.lower() in memory.emotional_context.lower():
                emotion_memories.append(memory)
                
        return emotion_memories[:limit]
        
    def get_conversation_context(self, limit: int = 5) -> str:
        """Get recent conversation memories as context string"""
        recent_memories = self.get_recent_memories(limit)
        context_parts = []
        
        for memory in recent_memories:
            if memory.memory_type == "conversation":
                context_parts.append(memory.content)
                
        return "\n".join(context_parts[-3:])
        
    def get_semantic_context(self, query: str, limit: int = 3) -> str:
        """Get semantically relevant memories as context"""
        if not self.vector_memory:
            return self.get_conversation_context(limit)
            
        semantic_memories = self.vector_memory.semantic_search(query, limit)
        context_parts = []
        
        for memory in semantic_memories:
            context_parts.append(memory['content'])
            
        return "\n".join(context_parts)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        stats = {
            'total_memories': len(self.memories),
            'memory_types': {
                mem_type: len([m for m in self.memories if m.memory_type == mem_type])
                for mem_type in set(m.memory_type for m in self.memories)
            },
            'vector_memory_enabled': self.vector_memory is not None,
            'oldest_memory': min([m.timestamp for m in self.memories]) if self.memories else None,
            'newest_memory': max([m.timestamp for m in self.memories]) if self.memories else None
        }
        
        if self.vector_memory:
            vector_stats = self.vector_memory.get_memory_stats()
            stats['vector_memory'] = vector_stats
            
        return stats