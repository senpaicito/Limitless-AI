import logging
import random
from typing import Dict, Any, List
from datetime import datetime
from .emotion_types import EmotionType, EmotionalState, EMOTIONAL_TRIGGERS, DEFAULT_EMOTIONAL_RESPONSES

class EmotionalResponseEngine:
    """Enhanced emotional response system for Phase 3"""
    
    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.logger = logging.getLogger(__name__)
        self.emotional_memory = []
        self.response_templates = self._load_response_templates()
        
    def _load_response_templates(self) -> Dict[EmotionType, List[str]]:
        """Load emotional response templates"""
        return {
            EmotionType.JOY: [
                "That's wonderful! 😊",
                "I'm so happy to hear that!",
                "That sounds amazing!",
                "What great news!",
                "This makes me smile! 😄"
            ],
            EmotionType.SADNESS: [
                "I'm sorry you're feeling this way. 💔",
                "That sounds really difficult.",
                "My heart goes out to you.",
                "I'm here for you.",
                "That must be really hard."
            ],
            EmotionType.ANGER: [
                "I understand why you'd feel that way.",
                "That sounds frustrating.",
                "I can sense your frustration.",
                "That would make anyone upset.",
                "I hear the anger in your voice."
            ],
            EmotionType.CURIOSITY: [
                "That's fascinating! Tell me more.",
                "I'm really curious about that.",
                "What an interesting thought!",
                "I'd love to learn more about that.",
                "That's got me thinking..."
            ],
            EmotionType.EXCITEMENT: [
                "That's so exciting! 🎉",
                "I'm getting excited just hearing about this!",
                "Wow, that sounds incredible!",
                "This is thrilling!",
                "I can feel the excitement!"
            ],
            EmotionType.NEUTRAL: [
                "I understand.",
                "Thanks for sharing that.",
                "That's interesting.",
                "I see what you mean.",
                "Tell me more about that."
            ]
        }
        
    def generate_emotional_response(self, user_input: str, emotional_state: EmotionalState) -> str:
        """Generate emotionally appropriate response"""
        # Analyze emotional content of user input
        input_emotion = self.analyze_emotional_content(user_input)
        
        # Get base response from templates
        base_response = self._get_base_response(emotional_state, input_emotion)
        
        # Add emotional flavor based on current state
        flavored_response = self._add_emotional_flavor(base_response, emotional_state)
        
        # Store emotional context for memory
        self._store_emotional_context(user_input, flavored_response, emotional_state, input_emotion)
        
        return flavored_response
        
    def analyze_emotional_content(self, text: str) -> Dict[EmotionType, float]:
        """Analyze emotional content of text with enhanced detection"""
        emotional_scores = {}
        text_lower = text.lower()
        
        # Check for emotional triggers
        for emotion_type, triggers in EMOTIONAL_TRIGGERS.items():
            score = 0
            for trigger in triggers:
                if trigger in text_lower:
                    score += 0.2
                    
            # Check for intensity modifiers
            intensity_modifiers = ["very", "really", "extremely", "so", "incredibly"]
            for modifier in intensity_modifiers:
                if f"{modifier} {trigger}" in text_lower:
                    score += 0.1
                    
            if score > 0:
                emotional_scores[emotion_type] = min(score, 1.0)
                
        # Check for punctuation-based emotional cues
        if "!" in text:
            emotional_scores[EmotionType.EXCITEMENT] = emotional_scores.get(EmotionType.EXCITEMENT, 0) + 0.3
        if "?" in text:
            emotional_scores[EmotionType.CURIOSITY] = emotional_scores.get(EmotionType.CURIOSITY, 0) + 0.2
            
        return emotional_scores
        
    def _get_base_response(self, current_emotion: EmotionalState, input_emotion: Dict[EmotionType, float]) -> str:
        """Get base response based on emotional context"""
        primary_emotion = current_emotion['primary_emotion']
        
        # If user input has strong emotion, respond to that
        if input_emotion:
            strongest_input_emotion = max(input_emotion.items(), key=lambda x: x[1])
            if strongest_input_emotion[1] > 0.5:
                templates = self.response_templates.get(strongest_input_emotion[0], [])
                if templates:
                    return random.choice(templates)
                    
        # Otherwise use current emotional state
        templates = self.response_templates.get(primary_emotion, [])
        if templates:
            return random.choice(templates)
            
        return random.choice(self.response_templates[EmotionType.NEUTRAL])
        
    def _add_emotional_flavor(self, response: str, emotional_state: EmotionalState) -> str:
        """Add emotional flavor to response based on intensity"""
        emotion = emotional_state['primary_emotion']
        intensity = emotional_state['intensity']
        
        # Add emotional modifiers based on intensity
        if intensity > 0.7:
            if emotion == EmotionType.JOY:
                response = response.replace(".", "! 😄")
            elif emotion == EmotionType.EXCITEMENT:
                response = response + " This is so exciting! 🎉"
            elif emotion == EmotionType.CURIOSITY:
                response = response + " I'm absolutely fascinated!"
                
        elif intensity > 0.9:
            # Very high intensity - add stronger emotional markers
            if emotion == EmotionType.JOY:
                response = "I'm absolutely overjoyed! " + response + " 🥳"
            elif emotion == EmotionType.SADNESS:
                response = "My heart is truly aching... " + response + " 💔"
                
        return response
        
    def _store_emotional_context(self, user_input: str, response: str, 
                               emotional_state: EmotionalState, input_emotion: Dict[EmotionType, float]):
        """Store emotional context for memory and learning"""
        emotional_context = {
            'timestamp': datetime.now(),
            'user_input': user_input,
            'ai_response': response,
            'ai_emotion': emotional_state,
            'user_emotion': input_emotion
        }
        
        self.emotional_memory.append(emotional_context)
        
        # Keep only last 100 emotional contexts
        if len(self.emotional_memory) > 100:
            self.emotional_memory = self.emotional_memory[-100:]
            
    def get_emotional_patterns(self) -> Dict[str, Any]:
        """Analyze emotional patterns from memory"""
        if not self.emotional_memory:
            return {}
            
        # Count emotional occurrences
        emotion_counts = {}
        for context in self.emotional_memory:
            ai_emotion = context['ai_emotion']['primary_emotion'].value
            emotion_counts[ai_emotion] = emotion_counts.get(ai_emotion, 0) + 1
            
        return {
            'total_interactions': len(self.emotional_memory),
            'emotion_distribution': emotion_counts,
            'most_common_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else 'neutral'
        }