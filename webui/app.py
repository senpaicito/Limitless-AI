from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import json
from typing import Dict, Any
import threading

class WebUI:
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        self.config = config
        self.character_manager = character_manager
        self.memory_manager = memory_manager
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        self.app = Flask(__name__)
        self.app.secret_key = 'ai_companion_secret_key'
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_routes()
        self.setup_socket_handlers()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('base.html')
            
        @self.app.route('/chat')
        def chat():
            return render_template('chat.html')
            
        @self.app.route('/services')
        def services():
            return render_template('services.html')
            
        @self.app.route('/settings')
        def settings():
            return render_template('settings.html')
            
        @self.app.route('/appearance')
        def appearance():
            return render_template('appearance.html')
            
        # API Routes
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'status': 'running',
                'character': self.character_manager.get_name(),
                'services': self.get_services_status()
            })
            
        @self.app.route('/api/chat/history')
        def api_chat_history():
            # Get recent conversation history
            recent_memories = self.memory_manager.get_recent_memories(limit=20)
            conversations = []
            
            for memory in recent_memories:
                if memory.memory_type == "conversation" and "User:" in memory.content:
                    parts = memory.content.split("\nAI: ")
                    if len(parts) == 2:
                        conversations.append({
                            'user': parts[0].replace("User: ", ""),
                            'ai': parts[1],
                            'timestamp': memory.timestamp.isoformat(),
                            'emotion': memory.emotional_context
                        })
                        
            return jsonify(conversations[::-1])  # Reverse to show newest first
            
        @self.app.route('/api/memory/stats')
        def api_memory_stats():
            stats = self.memory_manager.get_memory_stats()
            return jsonify(stats)
            
        @self.app.route('/api/character')
        def api_character():
            return jsonify({
                'name': self.character_manager.get_name(),
                'traits': self.character_manager.get_traits(),
                'personality': self.character_manager.get_personality()
            })
            
        @self.app.route('/api/emotions/current')
        def api_current_emotions():
            emotional_state = self.ai_engine.current_emotional_state
            return jsonify({
                'primary_emotion': emotional_state['primary_emotion'].value,
                'intensity': emotional_state['intensity'],
                'secondary_emotions': {
                    emotion.value: intensity 
                    for emotion, intensity in emotional_state['secondary_emotions'].items()
                }
            })
            
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            if request.method == 'POST':
                config_data = request.json
                # Update configuration (basic implementation)
                for key, value in config_data.items():
                    self.config.set(key, value)
                return jsonify({'status': 'updated'})
            else:
                return jsonify(self.config.config)
                
    def setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info('Client connected to WebUI')
            emit('connected', {'message': 'Connected to AI Companion'})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info('Client disconnected from WebUI')
            
        @self.socketio.on('send_message')
        def handle_send_message(data):
            user_message = data.get('message', '')
            self.logger.info(f'WebUI message: {user_message}')
            
            # Process message through AI engine
            def process_and_respond():
                try:
                    response = self.ai_engine.process_message(user_message)
                    emit('ai_response', {
                        'message': response,
                        'emotion': self.ai_engine.current_emotional_state['primary_emotion'].value,
                        'intensity': self.ai_engine.current_emotional_state['intensity']
                    })
                except Exception as e:
                    self.logger.error(f"Error processing WebUI message: {e}")
                    emit('ai_response', {
                        'message': "I'm sorry, I encountered an error processing your message.",
                        'emotion': 'neutral',
                        'intensity': 0.5
                    })
            
            # Run in thread to avoid blocking
            thread = threading.Thread(target=process_and_respond)
            thread.start()
            
        @self.socketio.on('get_services_status')
        def handle_get_services_status():
            emit('services_status', self.get_services_status())
            
        @self.socketio.on('update_settings')
        def handle_update_settings(data):
            try:
                for key, value in data.items():
                    self.config.set(key, value)
                self.config.save_config()
                emit('settings_updated', {'status': 'success'})
            except Exception as e:
                emit('settings_updated', {'status': 'error', 'message': str(e)})
                
    def get_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            'ollama': {
                'status': 'connected' if self.ai_engine.ollama_client.client else 'disconnected',
                'model': self.config.get('ollama.model'),
                'available_models': len(self.ai_engine.ollama_client.get_available_models())
            },
            'memory': {
                'status': 'active',
                'total_memories': len(self.memory_manager.memories),
                'vector_memory': self.config.get('memory.semantic_search_enabled', False)
            },
            'webui': {
                'status': 'running',
                'host': self.config.get('webui.host'),
                'port': self.config.get('webui.port')
            },
            'plugins': {
                'status': 'active',
                'loaded_plugins': self.ai_engine.plugin_manager.get_loaded_plugins()
            },
            'discord': {
                'status': 'disabled' if not self.config.get('integrations.discord.enabled') else 'connected',
                'enabled': self.config.get('integrations.discord.enabled', False)
            },
            'vtube_studio': {
                'status': 'disabled' if not self.config.get('integrations.vtube_studio.enabled') else 'connected', 
                'enabled': self.config.get('integrations.vtube_studio.enabled', False)
            },
            'tts': {
                'status': 'disabled' if not self.config.get('integrations.piper_tts.enabled') else 'connected',
                'enabled': self.config.get('integrations.piper_tts.enabled', False)
            }
        }
        
    def start(self):
        """Start the WebUI server"""
        host = self.config.get('webui.host', '127.0.0.1')
        port = self.config.get('webui.port', 5000)
        debug = self.config.get('webui.debug', False)
        
        self.logger.info(f"Starting WebUI on http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        
    def stop(self):
        """Stop the WebUI server"""
        self.logger.info("Stopping WebUI server")