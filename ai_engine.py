import logging
from typing import Dict, Any, List
from datetime import datetime
import numpy as np

from config.config_manager import ConfigManager
from character.character_manager import CharacterManager
from memory.basic_memory import BasicMemoryManager
from memory.vector_db import VectorMemory
from ai_core.ollama_client import OllamaClient
from ai_core.emotion_types import EmotionType, EmotionalState, EMOTIONAL_TRIGGERS
from plugins.plugin_manager import PluginManager

class AIEngine:
    """Core AI processing engine with Phase 3 enhancements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.shutdown_flag = False
        
        # Initialize core components
        self.config = ConfigManager()
        self.character_manager = CharacterManager()
        self.memory_manager = BasicMemoryManager(self.config)
        self.ollama_client = OllamaClient(self.config)
        self.plugin_manager = PluginManager(
            self.config, self.character_manager, self.memory_manager, self
        )
        
        # Enhanced emotional state system
        self.current_emotional_state: EmotionalState = self._initialize_emotional_state()
        self.emotional_history: List[EmotionalState] = []
        self.emotional_memory = []  # Add this missing attribute
        
        # Personality traits (dynamic)
        self.personality_traits = self._initialize_personality()
        
        # Learning system
        self.user_preferences = {}
        self.learned_facts = []
        
        # Integration states
        self.integration_states = {
            'discord': False,
            'vtube_studio': False,
            'tts': False
        }
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Vector memory (initialize as None, will be set in initialize())
        self.vector_memory = None
        
    def _initialize_emotional_state(self) -> EmotionalState:
        """Initialize emotional state from character configuration"""
        base_emotions = self.character_manager.get_emotional_state()
        
        return {
            'primary_emotion': EmotionType.NEUTRAL,
            'intensity': 0.5,
            'secondary_emotions': base_emotions,
            'timestamp': datetime.now().timestamp()
        }
        
    def _initialize_personality(self) -> Dict[str, float]:
        """Initialize personality traits from character"""
        traits = self.character_manager.get_traits()
        personality = {}
        
        # Convert traits to numerical values
        for trait in traits:
            personality[trait] = 0.7  # Default strength
            
        return personality
        
    def initialize(self) -> bool:
        """Initialize the AI engine with Phase 3 integrations"""
        try:
            self.logger.info("Initializing AI Engine (Phase 3)...")
            
            # Validate configurations
            if not self.config.validate_config():
                self.logger.error("Configuration validation failed")
                return False
                
            if not self.character_manager.validate_character():
                self.logger.error("Character validation failed")
                return False
                
            # Initialize plugins (including Phase 3 integrations)
            if not self.plugin_manager.load_plugins():
                self.logger.warning("Some plugins failed to load")
                
            # Initialize vector memory if enabled
            if self.config.get('memory.semantic_search_enabled', False):
                try:
                    self.vector_memory = VectorMemory(
                        self.config.get('memory.vector_db_path', './data/memories')
                    )
                    self.logger.info("Vector memory initialized for semantic search")
                except Exception as e:
                    self.logger.error(f"Failed to initialize vector memory: {e}")
                    self.vector_memory = None
            else:
                self.vector_memory = None
                
            # Update integration states
            self._update_integration_states()
                
            self.logger.info("AI Engine Phase 3 initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Engine: {e}")
            return False
            
    def _update_integration_states(self):
        """Update integration status based on loaded plugins"""
        loaded_plugins = self.plugin_manager.get_loaded_plugins()
        
        self.integration_states['discord'] = 'discord_bot' in loaded_plugins
        self.integration_states['vtube_studio'] = 'vtube_studio' in loaded_plugins
        self.integration_states['tts'] = 'piper_tts' in loaded_plugins
        
    def process_message(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Process a user message with enhanced emotional and integration support"""
        try:
            # Broadcast message received to plugins
            self.plugin_manager.broadcast_message_received(user_input, "user")
            
            # Update emotional state based on input
            self._update_emotional_state(user_input)
            
            # Learn from user input
            self._learn_from_interaction(user_input)
            
            # Prepare enhanced context
            enhanced_context = self._prepare_enhanced_context(user_input, context)
            
            # Generate system prompt with emotional and personality context
            emotional_context = self._get_emotional_context()
            personality_context = self._get_personality_context()
            integration_context = self._get_integration_context()
            
            system_prompt = self.character_manager.get_system_prompt(
                f"{emotional_context}\n{personality_context}\n{integration_context}"
            )
            
            # Prepare messages for Ollama
            messages = self._prepare_messages(user_input, enhanced_context)
            
            # Generate response
            response_data = self.ollama_client.generate_response(messages, system_prompt)
            
            if response_data['success']:
                response = response_data['content']
                
                # Store conversation in memory with emotional context
                emotional_context_str = self._get_emotional_context_string()
                self.memory_manager.add_conversation_memory(
                    user_input, response, emotional_context_str
                )
                
                # Also store in vector memory if available
                if self.vector_memory:
                    self.vector_memory.add_memory(
                        content=f"User: {user_input}\nAI: {response}",
                        memory_type="conversation",
                        emotional_context=emotional_context_str,
                        importance=0.7
                    )
                
                # Update conversation history
                self.conversation_history.extend([
                    {'role': 'user', 'content': user_input},
                    {'role': 'assistant', 'content': response}
                ])
                
                # Keep history manageable
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                    
                # Update personality based on interaction
                self._update_personality(user_input, response)
                    
                # Broadcast response to plugins (for TTS, VTube Studio, etc.)
                self.plugin_manager.broadcast_message_sent(response, "ai")
                
                return response
            else:
                error_msg = "I apologize, but I'm having trouble generating a response right now."
                self.logger.error(f"Ollama response failed: {response_data}")
                return error_msg
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return "I encountered an error while processing your message. Please try again."
            
    def _update_emotional_state(self, user_input: str) -> None:
        """Enhanced emotional state update with emotional triggers"""
        input_lower = user_input.lower()
        
        # Detect emotional triggers
        emotional_shifts = {}
        
        for emotion_type in EmotionType:
            emotion_triggers = EMOTIONAL_TRIGGERS.get(emotion_type, [])
            for trigger in emotion_triggers:
                if trigger in input_lower:
                    emotional_shifts[emotion_type] = emotional_shifts.get(emotion_type, 0) + 0.3
                    
        # Consider conversation context for emotional shifts
        if not emotional_shifts:
            # Check if this continues an emotional topic
            recent_emotion = self._get_recent_emotional_context()
            if recent_emotion and recent_emotion != EmotionType.NEUTRAL:
                emotional_shifts[recent_emotion] = 0.2
                
        # Update emotional state
        if emotional_shifts:
            primary_emotion = max(emotional_shifts.items(), key=lambda x: x[1])
            self.current_emotional_state = {
                'primary_emotion': primary_emotion[0],
                'intensity': min(primary_emotion[1], 1.0),
                'secondary_emotions': {k: v for k, v in emotional_shifts.items() if k != primary_emotion[0]},
                'timestamp': datetime.now().timestamp()
            }
            
            # Add to emotional history
            self.emotional_history.append(self.current_emotional_state.copy())
            if len(self.emotional_history) > 50:  # Keep last 50 emotional states
                self.emotional_history = self.emotional_history[-50:]
        else:
            # Gradually return to neutral
            current_intensity = self.current_emotional_state['intensity']
            if current_intensity > 0.3:
                self.current_emotional_state['intensity'] = current_intensity * 0.8
            else:
                self.current_emotional_state = {
                    'primary_emotion': EmotionType.NEUTRAL,
                    'intensity': 0.3,
                    'secondary_emotions': {},
                    'timestamp': datetime.now().timestamp()
                }
                
    def _get_recent_emotional_context(self) -> EmotionType:
        """Get recent emotional context from history"""
        if not self.emotional_history:
            return EmotionType.NEUTRAL
            
        # Get most recent non-neutral emotion
        for emotional_state in reversed(self.emotional_history[-10:]):
            if emotional_state['primary_emotion'] != EmotionType.NEUTRAL:
                return emotional_state['primary_emotion']
                
        return EmotionType.NEUTRAL
        
    def _learn_from_interaction(self, user_input: str) -> None:
        """Learn from user interactions"""
        if not self.config.get('personality.learning_enabled', True):
            return
            
        # Extract potential facts (simple implementation)
        fact_indicators = ["i like", "i love", "i hate", "i'm", "my favorite", "i enjoy"]
        input_lower = user_input.lower()
        
        for indicator in fact_indicators:
            if indicator in input_lower:
                # Extract the fact
                fact = user_input
                self.learned_facts.append({
                    'fact': fact,
                    'timestamp': datetime.now(),
                    'confidence': 0.8
                })
                self.logger.info(f"Learned fact: {fact}")
                break
                
    def _update_personality(self, user_input: str, ai_response: str) -> None:
        """Update personality based on interactions"""
        if not self.config.get('personality.learning_enabled', True):
            return
            
        adaptation_rate = self.config.get('personality.adaptation_rate', 0.1)
        
        # Simple personality adaptation based on conversation tone
        if "?" in user_input and "?" in ai_response:
            # Both asking questions - increase curiosity
            self.personality_traits['curious'] = min(1.0, 
                self.personality_traits.get('curious', 0.7) + adaptation_rate * 0.1)
                
        # More sophisticated adaptation can be added here
        
    def _prepare_enhanced_context(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Prepare enhanced context with semantic search"""
        context_parts = []
        
        # Get recent memories
        recent_memories = self.memory_manager.get_recent_memories(limit=3)
        for memory in recent_memories:
            if memory.memory_type == "conversation":
                context_parts.append(memory.content)
                
        # Get semantically relevant memories if vector memory is available
        if self.vector_memory:
            semantic_memories = self.vector_memory.semantic_search(user_input, limit=2)
            for memory in semantic_memories:
                context_parts.append(f"Relevant memory: {memory['content']}")
                
        # Add learned facts if relevant
        if self.learned_facts:
            recent_facts = self.learned_facts[-3:]  # Last 3 learned facts
            for fact_data in recent_facts:
                context_parts.append(f"Known fact: {fact_data['fact']}")
                
        return "\n".join(context_parts)
        
    def _prepare_messages(self, user_input: str, context: str = "") -> List[Dict[str, str]]:
        """Prepare messages for Ollama with enhanced context"""
        messages = []
        
        # Add context if available
        if context:
            messages.append({
                'role': 'system',
                'content': f"Conversation context:\n{context}"
            })
            
        # Add current user input
        messages.append({
            'role': 'user',
            'content': user_input
        })
        
        return messages
        
    def _get_emotional_context(self) -> str:
        """Get emotional context for system prompt"""
        emotion = self.current_emotional_state['primary_emotion']
        intensity = self.current_emotional_state['intensity']
        
        intensity_desc = "slightly" if intensity < 0.4 else "moderately" if intensity < 0.7 else "very"
        
        emotional_context = f"Current emotional state: {intensity_desc} {emotion.value}"
        
        # Add secondary emotions if significant
        significant_secondaries = [
            f"{emotion.value} ({intensity:.1f})" 
            for emotion, intensity in self.current_emotional_state['secondary_emotions'].items()
            if intensity > 0.3
        ]
        
        if significant_secondaries:
            emotional_context += f". Also feeling: {', '.join(significant_secondaries)}"
            
        return emotional_context
        
    def _get_emotional_context_string(self) -> str:
        """Get emotional context as string for memory storage"""
        emotion = self.current_emotional_state['primary_emotion']
        intensity = self.current_emotional_state['intensity']
        
        if intensity < 0.4:
            return f"slightly_{emotion.value}"
        elif intensity < 0.7:
            return f"moderately_{emotion.value}"
        else:
            return f"very_{emotion.value}"
        
    def _get_personality_context(self) -> str:
        """Get personality context for system prompt"""
        strong_traits = [
            trait for trait, strength in self.personality_traits.items() 
            if strength > 0.7
        ]
        
        if strong_traits:
            return f"Current personality emphasis: {', '.join(strong_traits)}"
        else:
            return "Personality: balanced"
            
    def _get_integration_context(self) -> str:
        """Get integration context for system prompt"""
        active_integrations = []
        
        if self.integration_states['discord']:
            active_integrations.append("Discord")
        if self.integration_states['vtube_studio']:
            active_integrations.append("VTube Studio (avatar)")
        if self.integration_states['tts']:
            active_integrations.append("Text-to-Speech")
            
        if active_integrations:
            return f"Active integrations: {', '.join(active_integrations)}"
        else:
            return "No active integrations"

    # ========== MISSING METHODS ADDED BELOW ==========

    def get_status(self) -> Dict[str, Any]:
        """Get AI engine status - THIS WAS MISSING"""
        status = {
            'initialized': True,
            'character': self.character_manager.get_name(),
            'model': self.config.get('ollama.model'),
            'memory_count': len(self.memory_manager.memories),
            'emotional_state': self.current_emotional_state,
            'personality_traits': self.personality_traits,
            'learned_facts_count': len(self.learned_facts),
            'loaded_plugins': self.plugin_manager.get_loaded_plugins(),
            'vector_memory_enabled': self.vector_memory is not None,
            'integration_status': self.get_integration_status()
        }
        
        if self.vector_memory:
            vector_stats = self.vector_memory.get_memory_stats()
            status['vector_memory_stats'] = vector_stats
            
        return status
        
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        return {
            'discord': {
                'enabled': self.integration_states['discord'],
                'plugin_loaded': 'discord_bot' in self.plugin_manager.get_loaded_plugins(),
                'config_enabled': self.config.get('integrations.discord.enabled', False)
            },
            'vtube_studio': {
                'enabled': self.integration_states['vtube_studio'],
                'plugin_loaded': 'vtube_studio' in self.plugin_manager.get_loaded_plugins(),
                'config_enabled': self.config.get('integrations.vtube_studio.enabled', False)
            },
            'tts': {
                'enabled': self.integration_states['tts'],
                'plugin_loaded': 'piper_tts' in self.plugin_manager.get_loaded_plugins(),
                'config_enabled': self.config.get('integrations.piper_tts.enabled', False)
            }
        }
        
    def get_emotional_analysis(self, text: str) -> Dict[EmotionType, float]:
        """Analyze emotional content of text"""
        emotional_scores = {}
        text_lower = text.lower()
        
        for emotion_type, triggers in EMOTIONAL_TRIGGERS.items():
            score = 0
            for trigger in triggers:
                if trigger in text_lower:
                    score += 0.1
            if score > 0:
                emotional_scores[emotion_type] = min(score, 1.0)
                
        return emotional_scores
        
    def shutdown(self) -> None:
        """Shutdown the AI engine"""
        self.logger.info("Shutting down AI Engine...")
        self.plugin_manager.cleanup_all()
        
        # Save vector memory if enabled
        if self.vector_memory:
            self.vector_memory.save_memories()
            
        self.logger.info("AI Engine shutdown complete")