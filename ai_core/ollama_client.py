import ollama
import logging
from typing import Dict, Any, List, Optional
from config.config_manager import ConfigManager

class OllamaClient:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize Ollama client with configuration"""
        try:
            base_url = self.config.get('ollama.base_url', 'http://localhost:11434')
            self.client = ollama.Client(host=base_url)
            
            # Test connection
            models = self.client.list()
            self.logger.info(f"Ollama client initialized successfully. Models: {len(models['models'])}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            raise

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict[str, Any]:
        """Generate response from Ollama"""
        try:
            model = self.config.get('ollama.model', 'llama2')
            temperature = self.config.get('ollama.temperature', 0.7)
            max_tokens = self.config.get('ollama.max_tokens', 500)

            # Prepare the messages with system prompt
            ollama_messages = []
            if system_prompt:
                ollama_messages.append({'role': 'system', 'content': system_prompt})
            ollama_messages.extend(messages)

            response = self.client.chat(
                model=model,
                messages=ollama_messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )

            return {
                'content': response['message']['content'],
                'model': model,
                'tokens_used': len(response['message']['content'].split()),
                'success': True
            }

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {
                'content': "I'm having trouble responding right now. Please try again.",
                'model': 'error',
                'tokens_used': 0,
                'success': False
            }

    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []

    def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        available_models = self.get_available_models()
        return any(model_name in model for model in available_models)

    def pull_model(self, model_name: str) -> bool:
        """Pull a model if not available"""
        try:
            self.logger.info(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            self.logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error pulling model {model_name}: {e}")
            return False