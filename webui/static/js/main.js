// Main JavaScript for AI Companion WebUI

class AICompanionUI {
    constructor() {
        this.socket = io();
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.setupEventListeners();
        this.initializeUI();
    }

    setupEventListeners() {
        // Socket event listeners
        this.socket.on('connect', () => this.handleConnect());
        this.socket.on('disconnect', () => this.handleDisconnect());
        this.socket.on('ai_response', (data) => this.handleAIResponse(data));
        this.socket.on('services_status', (data) => this.updateServicesStatus(data));
        this.socket.on('settings_updated', (data) => this.handleSettingsUpdated(data));
        this.socket.on('connected', (data) => this.handleServerConnected(data));

        // Chat event listeners
        this.setupChatEvents();
    }

    setupChatEvents() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        if (sendButton && messageInput) {
            sendButton.addEventListener('click', () => this.sendMessage());
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Clear chat button
        const clearChatBtn = document.getElementById('clear-chat');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => this.clearChat());
        }
    }

    initializeUI() {
        this.applyTheme(this.currentTheme);
        this.loadChatHistory();
        this.loadMemoryStats();
        this.startEmotionUpdates();
    }

    handleConnect() {
        this.updateConnectionStatus('connected');
        console.log('Connected to AI Companion server');
    }

    handleDisconnect() {
        this.updateConnectionStatus('disconnected');
        console.log('Disconnected from AI Companion server');
    }

    handleServerConnected(data) {
        console.log('Server connection confirmed:', data);
        this.updateConnectionStatus('connected');
    }

    handleAIResponse(data) {
        console.log('AI Response received:', data);
        this.addMessage('ai', data.message, data.emotion);
        
        // Update emotional state display
        this.updateEmotionalState(data.emotion, data.intensity);
    }

    sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Add user message to chat immediately
        this.addMessage('user', message);
        messageInput.value = '';

        // Send to server
        this.socket.emit('send_message', { message: message });
        console.log('Message sent to server:', message);
    }

    addMessage(sender, message, emotion = 'neutral') {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const time = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-sender">${sender === 'user' ? 'You' : document.querySelector('.character-name')?.textContent || 'AI'}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
            ${sender === 'ai' ? `<div class="message-emotion">Feeling: ${emotion}</div>` : ''}
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, '<br>');
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('span');

        if (status === 'connected') {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Disconnected';
        }
    }

    updateEmotionalState(emotion, intensity) {
        const primaryEmotion = document.getElementById('primary-emotion');
        const intensityFill = document.getElementById('intensity-fill');
        const intensityText = document.getElementById('intensity-text');

        if (primaryEmotion) primaryEmotion.textContent = emotion || 'neutral';
        if (intensityFill) intensityFill.style.width = `${(intensity || 0.5) * 100}%`;
        if (intensityText) intensityText.textContent = `${Math.round((intensity || 0.5) * 100)}%`;
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update stylesheet
        const themeStylesheet = document.getElementById('theme-stylesheet');
        if (themeStylesheet) {
            themeStylesheet.href = `/static/css/${theme}.css`;
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            const conversations = await response.json();
            
            const chatMessages = document.getElementById('chat-messages');
            if (!chatMessages) return;

            // Clear existing messages
            chatMessages.innerHTML = '';

            // Add historical messages
            conversations.forEach(conv => {
                this.addMessage('user', conv.user, '', new Date(conv.timestamp).toLocaleTimeString());
                this.addMessage('ai', conv.ai, conv.emotion, new Date(conv.timestamp).toLocaleTimeString());
            });
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    async loadMemoryStats() {
        try {
            const response = await fetch('/api/memory/stats');
            const stats = await response.json();
            
            const totalMemories = document.getElementById('total-memories');
            const vectorDbStatus = document.getElementById('vector-db-status');
            
            if (totalMemories) totalMemories.textContent = stats.total_memories || 0;
            if (vectorDbStatus) {
                vectorDbStatus.textContent = stats.vector_memory_enabled ? 'Enabled' : 'Disabled';
            }
        } catch (error) {
            console.error('Error loading memory stats:', error);
        }
    }

    startEmotionUpdates() {
        // Periodically update emotional state
        setInterval(() => {
            this.fetchCurrentEmotions();
        }, 5000); // Update every 5 seconds
        
        // Initial load
        this.fetchCurrentEmotions();
    }

    async fetchCurrentEmotions() {
        try {
            const response = await fetch('/api/emotions/current');
            const emotions = await response.json();
            
            this.updateEmotionalState(
                emotions.primary_emotion, 
                emotions.intensity
            );
        } catch (error) {
            console.error('Error fetching emotions:', error);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    updateServicesStatus(services) {
        console.log('Services status updated:', services);
    }

    handleSettingsUpdated(data) {
        if (data.status === 'success') {
            this.showNotification('Settings updated successfully', 'success');
        } else {
            this.showNotification('Failed to update settings: ' + data.message, 'error');
        }
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiCompanionUI = new AICompanionUI();
});