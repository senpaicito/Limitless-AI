from enum import Enum
from typing import Dict, List, TypedDict

class EmotionType(Enum):
    JOY = "joy"
    SADNESS = "sadness" 
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    CURIOSITY = "curiosity"
    EXCITEMENT = "excitement"
    CONTENTMENT = "contentment"
    NEUTRAL = "neutral"

class EmotionalState(TypedDict):
    primary_emotion: EmotionType
    intensity: float  # 0.0 to 1.0
    secondary_emotions: Dict[EmotionType, float]
    timestamp: float

class PersonalityTrait(TypedDict):
    name: str
    strength: float  # 0.0 to 1.0
    description: str

# Emotional triggers for Phase 2
EMOTIONAL_TRIGGERS = {
    EmotionType.JOY: ["happy", "great", "wonderful", "amazing", "love", "excited"],
    EmotionType.SADNESS: ["sad", "hurt", "miss", "lost", "sorry", "unhappy"],
    EmotionType.ANGER: ["angry", "mad", "frustrated", "annoyed", "hate", "upset"],
    EmotionType.CURIOSITY: ["wonder", "curious", "question", "why", "how", "learn"]
}

# Default emotional responses
DEFAULT_EMOTIONAL_RESPONSES = {
    EmotionType.JOY: "I'm really happy to hear that!",
    EmotionType.SADNESS: "I'm sorry you're feeling that way. I'm here for you.",
    EmotionType.CURIOSITY: "That's really interesting! Tell me more about that.",
    EmotionType.NEUTRAL: "I understand. Thanks for sharing that with me."
}