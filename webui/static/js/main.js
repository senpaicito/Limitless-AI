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

        // Theme toggle
        document.getElementById('theme-toggle')?.addEventListener('click', () => this.toggleTheme());

        // Auto-reconnect
        setInterval(() => {
            if (!this.socket.connected) {
                this.socket.connect();
            }
        }, 5000);
    }

    initializeUI() {
        this.applyTheme(this.currentTheme);
        this.loadUIState();
    }

    handleConnect() {
        this.updateConnectionStatus('connected');
        console.log('Connected to AI Companion server');
    }

    handleDisconnect() {
        this.updateConnectionStatus('disconnected');
        console.log('Disconnected from AI Companion server');
    }

    handleAIResponse(data) {
        // This will be implemented in chat-specific JS
        console.log('AI Response:', data);
    }

    updateServicesStatus(services) {
        // This will be implemented in services-specific JS
        console.log('Services status updated:', services);
    }

    handleSettingsUpdated(data) {
        if (data.status === 'success') {
            this.showNotification('Settings updated successfully', 'success');
        } else {
            this.showNotification('Failed to update settings: ' + data.message, 'error');
        }
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

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update stylesheet
        const themeStylesheet = document.getElementById('theme-stylesheet');
        if (themeStylesheet) {
            themeStylesheet.href = `/static/css/${theme}.css`;
        }
    }

    loadUIState() {
        // Load saved UI state from localStorage
        const savedState = localStorage.getItem('ai_companion_ui_state');
        if (savedState) {
            try {
                const state = JSON.parse(savedState);
                // Apply saved state
                if (state.theme) {
                    this.applyTheme(state.theme);
                }
            } catch (e) {
                console.error('Error loading UI state:', e);
            }
        }
    }

    saveUIState() {
        const state = {
            theme: this.currentTheme,
            timestamp: Date.now()
        };
        localStorage.setItem('ai_companion_ui_state', JSON.stringify(state));
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

        // Add styles if not already added
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-color);
                    border-radius: var(--border-radius);
                    padding: 1rem;
                    max-width: 300px;
                    box-shadow: var(--shadow);
                    animation: slideIn 0.3s ease;
                }
                .notification-success {
                    border-left: 4px solid var(--success-color);
                }
                .notification-error {
                    border-left: 4px solid var(--error-color);
                }
                .notification-warning {
                    border-left: 4px solid var(--warning-color);
                }
                .notification-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .notification-close {
                    background: none;
                    border: none;
                    color: var(--text-secondary);
                    cursor: pointer;
                    font-size: 1.2rem;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }

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

    // Utility function for making API calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('API call failed: ' + error.message, 'error');
            throw error;
        }
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiCompanionUI = new AICompanionUI();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AICompanionUI;
}