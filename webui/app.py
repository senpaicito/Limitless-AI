from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import json
from typing import Dict, Any

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
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        self.setup_routes()
        self.setup_socket_handlers()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            try:
                character_name = self.character_manager.get_name()
                return render_template('base.html', character_name=character_name)
            except Exception as e:
                self.logger.error("Error in index route: %s", e)
                return render_template('base.html', character_name='AI Companion')
            
        @self.app.route('/chat')
        def chat():
            try:
                character_name = self.character_manager.get_name()
                return render_template('chat.html', character_name=character_name)
            except Exception as e:
                self.logger.error("Error in chat route: %s", e)
                return render_template('chat.html', character_name='AI Companion')
            
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
            try:
                character_name = self.character_manager.get_name()
                return jsonify({
                    'status': 'running',
                    'character': character_name,
                    'services': self.get_services_status()
                })
            except Exception as e:
                self.logger.error("Error in api_status: %s", e)
                return jsonify({
                    'status': 'running',
                    'character': 'AI Companion',
                    'services': {}
                })
            
        @self.app.route('/api/chat/history')
        def api_chat_history():
            try:
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
                            
                return jsonify(conversations[::-1])
            except Exception as e:
                self.logger.error("Error loading chat history: %s", e)
                return jsonify([])
            
        @self.app.route('/api/memory/stats')
        def api_memory_stats():
            try:
                stats = self.memory_manager.get_memory_stats()
                return jsonify(stats)
            except Exception as e:
                self.logger.error("Error getting memory stats: %s", e)
                return jsonify({
                    'total_memories': 0,
                    'vector_memory_enabled': False
                })
            
        @self.app.route('/api/character')
        def api_character():
            try:
                return jsonify({
                    'name': self.character_manager.get_name(),
                    'traits': self.character_manager.get_traits(),
                    'personality': self.character_manager.get_personality()
                })
            except Exception as e:
                self.logger.error("Error getting character info: %s", e)
                return jsonify({
                    'name': 'AI Companion',
                    'traits': [],
                    'personality': 'Friendly AI assistant'
                })
            
        @self.app.route('/api/emotions/current')
        def api_current_emotions():
            try:
                emotional_state = self.ai_engine.current_emotional_state
                primary_emotion = emotional_state['primary_emotion']
                emotion_value = primary_emotion.value if hasattr(primary_emotion, 'value') else str(primary_emotion)
                
                return jsonify({
                    'primary_emotion': emotion_value,
                    'intensity': emotional_state['intensity'],
                    'secondary_emotions': {
                        (emotion.value if hasattr(emotion, 'value') else str(emotion)): intensity 
                        for emotion, intensity in emotional_state['secondary_emotions'].items()
                    }
                })
            except Exception as e:
                self.logger.error("Error getting emotions: %s", e)
                return jsonify({
                    'primary_emotion': 'neutral',
                    'intensity': 0.5,
                    'secondary_emotions': {}
                })
                
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            if request.method == 'POST':
                try:
                    config_data = request.json
                    for key, value in config_data.items():
                        self.config.set(key, value)
                    return jsonify({'status': 'updated'})
                except Exception as e:
                    self.logger.error("Error updating config: %s", e)
                    return jsonify({'status': 'error', 'message': str(e)})
            else:
                return jsonify(self.config.config)
                
    def setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info('Client connected to WebUI: %s', request.sid)
            try:
                character_name = self.character_manager.get_name()
                emit('connected', {
                    'message': 'Connected to AI Companion', 
                    'character': character_name
                })
            except Exception as e:
                self.logger.error("Error in connect handler: %s", e)
                emit('connected', {
                    'message': 'Connected to AI Companion', 
                    'character': 'AI Companion'
                })
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info('Client disconnected from WebUI: %s', request.sid)
            
        @self.socketio.on('send_message')
        def handle_send_message(data):
            user_message = data.get('message', '').strip()
            if not user_message:
                self.logger.warning('Received empty message')
                return
                
            self.logger.info('WebUI message received: %s', user_message)
            
            try:
                # Process message through AI engine
                self.logger.info('Processing message through AI engine...')
                response = self.ai_engine.process_message(user_message)
                self.logger.info('AI engine response: %s', response)
                
                # Get emotional state
                emotion_state = self.ai_engine.current_emotional_state
                primary_emotion = emotion_state['primary_emotion']
                emotion_value = primary_emotion.value if hasattr(primary_emotion, 'value') else str(primary_emotion)
                
                self.logger.info('Sending response to WebUI client: %s', request.sid)
                
                # Send response back to the client that sent the message
                emit('ai_response', {
                    'message': response,
                    'emotion': emotion_value,
                    'intensity': emotion_state['intensity']
                })
                
            except Exception as e:
                self.logger.error('Error processing WebUI message: %s', e)
                emit('ai_response', {
                    'message': "I'm sorry, I encountered an error. Please try again.",
                    'emotion': 'neutral',
                    'intensity': 0.5
                })
            
        @self.socketio.on('get_services_status')
        def handle_get_services_status():
            try:
                emit('services_status', self.get_services_status())
            except Exception as e:
                self.logger.error("Error getting services status: %s", e)
                emit('services_status', {'error': str(e)})
            
        @self.socketio.on('update_settings')
        def handle_update_settings(data):
            try:
                for key, value in data.items():
                    self.config.set(key, value)
                self.config.save_config()
                emit('settings_updated', {'status': 'success'})
            except Exception as e:
                self.logger.error('Error updating settings: %s', e)
                emit('settings_updated', {'status': 'error', 'message': str(e)})
                
    def get_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        try:
            integration_status = self.ai_engine.get_integration_status()
            
            return {
                'ollama': {
                    'status': 'connected',
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
                    'status': 'connected' if integration_status['discord']['enabled'] else 'disabled',
                    'enabled': integration_status['discord']['config_enabled']
                },
                'vtube_studio': {
                    'status': 'connected' if integration_status['vtube_studio']['enabled'] else 'disabled', 
                    'enabled': integration_status['vtube_studio']['config_enabled']
                },
                'tts': {
                    'status': 'connected' if integration_status['tts']['enabled'] else 'disabled',
                    'enabled': integration_status['tts']['config_enabled']
                }
            }
        except Exception as e:
            self.logger.error('Error getting services status: %s', e)
            return {'error': str(e)}
        
    def start(self):
        """Start the WebUI server"""
        host = self.config.get('webui.host', '127.0.0.1')
        port = self.config.get('webui.port', 5000)
        debug = self.config.get('webui.debug', False)
        
        self.logger.info("Starting WebUI on http://%s:%s", host, port)
        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        except Exception as e:
            self.logger.error("WebUI server error: %s", e)
        
    def stop(self):
        """Stop the WebUI server"""
        self.logger.info("Stopping WebUI server")