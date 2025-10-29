import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import pickle

class VectorMemory:
    """Vector database for semantic memory storage and retrieval"""
    
    def __init__(self, storage_path: str = "./data/vector_memories"):
        self.storage_path = Path(storage_path)
        self.memories = []
        self.embeddings = None
        self.logger = logging.getLogger(__name__)
        self.initialize_storage()
        
    def initialize_storage(self):
        """Initialize vector storage"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.load_memories()
            self.logger.info(f"Vector memory initialized with {len(self.memories)} memories")
        except Exception as e:
            self.logger.error(f"Error initializing vector memory: {e}")
            
    def add_memory(self, content: str, memory_type: str = "conversation", 
                   emotional_context: str = "", importance: float = 0.5,
                   metadata: Dict[str, Any] = None) -> str:
        """Add a memory with vector embedding"""
        try:
            memory_id = f"vec_mem_{len(self.memories)}_{datetime.now().timestamp()}"
            
            # Generate embedding (simple TF-IDF style for Phase 2, can upgrade to sentence transformers)
            embedding = self._generate_embedding(content)
            
            memory = {
                'id': memory_id,
                'content': content,
                'type': memory_type,
                'emotional_context': emotional_context,
                'importance': importance,
                'embedding': embedding,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {},
                'tags': self._extract_tags(content, emotional_context)
            }
            
            self.memories.append(memory)
            self.save_memories()
            
            self.logger.debug(f"Added vector memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding vector memory: {e}")
            return ""
            
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text (simplified for Phase 2)"""
        # Simple bag-of-words style embedding
        words = text.lower().split()
        unique_words = list(set(words))
        embedding = np.zeros(100)  # Fixed size for simplicity
        
        for i, word in enumerate(unique_words[:100]):  # Limit to first 100 unique words
            embedding[i] = words.count(word) / len(words)  # Normalized frequency
            
        return embedding
        
    def _extract_tags(self, content: str, emotional_context: str) -> List[str]:
        """Extract tags from content and emotional context"""
        tags = []
        
        # Add emotional context as tag
        if emotional_context:
            tags.append(f"emotion:{emotional_context}")
            
        # Extract key phrases (simplified)
        words = content.lower().split()
        significant_words = [word for word in words if len(word) > 4][:5]
        tags.extend(significant_words)
        
        return tags
        
    def semantic_search(self, query: str, limit: int = 5, 
                       memory_types: List[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on memories"""
        try:
            if not self.memories:
                return []
                
            query_embedding = self._generate_embedding(query)
            similarities = []
            
            for memory in self.memories:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, memory['embedding'])
                
                # Filter by memory type if specified
                if memory_types and memory['type'] not in memory_types:
                    continue
                    
                similarities.append((similarity, memory))
                
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [mem for _, mem in similarities[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
            
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def search_by_emotion(self, emotion: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by emotional context"""
        emotion_memories = []
        
        for memory in self.memories:
            if emotion.lower() in memory['emotional_context'].lower():
                emotion_memories.append(memory)
                
        return emotion_memories[:limit]
        
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by tags"""
        tag_memories = []
        
        for memory in self.memories:
            memory_tags = [tag.lower() for tag in memory.get('tags', [])]
            search_tags = [tag.lower() for tag in tags]
            
            if any(search_tag in memory_tag for search_tag in search_tags for memory_tag in memory_tags):
                tag_memories.append(memory)
                
        return tag_memories[:limit]
        
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent memories"""
        sorted_memories = sorted(self.memories, 
                               key=lambda x: x['timestamp'], 
                               reverse=True)
        return sorted_memories[:limit]
        
    def get_important_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most important memories"""
        sorted_memories = sorted(self.memories, 
                               key=lambda x: x['importance'], 
                               reverse=True)
        return sorted_memories[:limit]
        
    def save_memories(self):
        """Save memories to disk"""
        try:
            memory_file = self.storage_path / "memories.json"
            embedding_file = self.storage_path / "embeddings.pkl"
            
            # Save memory metadata
            memories_to_save = []
            for memory in self.memories:
                memory_copy = memory.copy()
                memory_copy['embedding'] = memory_copy['embedding'].tolist()  # Convert numpy to list
                memories_to_save.append(memory_copy)
                
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories_to_save, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(f"Saved {len(self.memories)} memories to disk")
            
        except Exception as e:
            self.logger.error(f"Error saving memories: {e}")
            
    def load_memories(self):
        """Load memories from disk"""
        try:
            memory_file = self.storage_path / "memories.json"
            
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memories_data = json.load(f)
                    
                # Convert embeddings back to numpy arrays
                for memory in memories_data:
                    memory['embedding'] = np.array(memory['embedding'])
                    
                self.memories = memories_data
                self.logger.info(f"Loaded {len(self.memories)} memories from disk")
                
        except Exception as e:
            self.logger.error(f"Error loading memories: {e}")
            self.memories = []
            
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        if not self.memories:
            return {'total_memories': 0}
            
        memory_types = {}
        emotions = {}
        
        for memory in self.memories:
            # Count by type
            mem_type = memory['type']
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            # Count by emotion
            emotion = memory['emotional_context'] or 'neutral'
            emotions[emotion] = emotions.get(emotion, 0) + 1
            
        return {
            'total_memories': len(self.memories),
            'memory_types': memory_types,
            'emotions': emotions,
            'average_importance': np.mean([m['importance'] for m in self.memories]),
            'oldest_memory': min([m['timestamp'] for m in self.memories]) if self.memories else None,
            'newest_memory': max([m['timestamp'] for m in self.memories]) if self.memories else None
        }