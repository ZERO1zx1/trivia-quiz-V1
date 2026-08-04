/**
 * TriviaVerse Chat System
 * Real-time chat with Socket.IO
 */

const ChatSystem = {
    socket: null,
    channelId: null,
    userId: null,
    username: null,

    init(options = {}) {
        this.channelId = options.channelId || 1;
        this.userId = options.userId;
        this.username = options.username;

        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupListeners();
        }

        this.setupUI();
        this.loadMessages();
    },

    setupListeners() {
        if (!this.socket) return;

        // Join channel
        this.socket.emit('join_chat', { channel_id: this.channelId });

        // New message
        this.socket.on('new_message', (data) => {
            this.appendMessage(data);
            this.scrollToBottom();
        });

        // Typing indicator
        this.socket.on('user_typing', (data) => {
            this.showTypingIndicator(data);
        });

        // User joined
        this.socket.on('joined', (data) => {
            this.addSystemMessage(`${data.username} joined the chat`);
        });

        // Message edited
        this.socket.on('message_edited', (data) => {
            this.updateMessage(data);
        });

        // Message deleted
        this.socket.on('message_deleted', (data) => {
            this.removeMessage(data.message_id);
        });
    },

    setupUI() {
        const form = document.getElementById('sendMessageForm') || document.getElementById('chat-form');
        const input = document.getElementById('messageInput') || document.getElementById('chat-input');
        const container = document.getElementById('chatMessages') || document.getElementById('chat-messages');

        if (form && input) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage(input.value.trim());
                input.value = '';
            });

            // Typing indicator
            let typingTimeout;
            input.addEventListener('input', () => {
                if (this.socket) {
                    this.socket.emit('typing', {
                        channel_id: this.channelId,
                        is_typing: true
                    });
                    clearTimeout(typingTimeout);
                    typingTimeout = setTimeout(() => {
                        this.socket.emit('typing', {
                            channel_id: this.channelId,
                            is_typing: false
                        });
                    }, 2000);
                }
            });
        }
    },

    sendMessage(content) {
        if (!content.trim()) return;

        if (this.socket) {
            this.socket.emit('send_message', {
                channel_id: this.channelId,
                content: content.trim()
            });
        } else {
            // Fallback to HTTP
            fetch(`/chat/send`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
                },
                body: JSON.stringify({ 
                    channel_id: this.channelId,
                    content: content.trim() 
                })
            });
        }
    },

    async loadMessages(limit = 50) {
        try {
            const response = await fetch(`/chat/api/${this.channelId}/messages?limit=${limit}`);
            const data = await response.json();
            const container = document.getElementById('chatMessages') || document.getElementById('chat-messages');
            if (container) {
                container.innerHTML = '';
                (data.messages || []).forEach(msg => this.appendMessage(msg));
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    },

    appendMessage(msg) {
        const container = document.getElementById('chatMessages') || document.getElementById('chat-messages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = 'chat-message';
        div.id = `msg-${msg.id}`;

        const isOwn = msg.user_id === this.userId;
        if (isOwn) div.classList.add('mine');

        div.innerHTML = `
            <div class="msg-header">
                <strong>${this.escapeHtml(msg.username || 'Unknown')}</strong>
                <span class="msg-time">${this.formatTime(msg.created_at)}</span>
            </div>
            <div class="msg-content">${this.escapeHtml(msg.content)}</div>
        `;

        container.appendChild(div);
    },

    addSystemMessage(text) {
        const container = document.getElementById('chatMessages') || document.getElementById('chat-messages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = 'text-center text-gray-500 text-xs py-1';
        div.textContent = text;
        container.appendChild(div);
        this.scrollToBottom();
    },

    showTypingIndicator(data) {
        const indicator = document.getElementById('typing-indicator');
        if (!indicator) return;

        if (data.is_typing && data.username !== this.username) {
            indicator.textContent = `${data.username} is typing...`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    },

    removeMessage(messageId) {
        const el = document.getElementById(`msg-${messageId}`);
        if (el) el.remove();
    },

    updateMessage(data) {
        const el = document.getElementById(`msg-${data.message_id || data.id}`);
        if (el) {
            const content = el.querySelector('.msg-content');
            if (content) content.textContent = data.new_content || data.content;
        }
    },

    scrollToBottom() {
        const container = document.getElementById('chatMessages') || document.getElementById('chat-messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    const channelInput = document.querySelector('input[name="channel_id"]');
    if (channelInput) {
        ChatSystem.init({
            channelId: parseInt(channelInput.value),
            userId: parseInt(document.body.dataset.userId || '0'),
            username: document.body.dataset.username || ''
        });
    }
});
