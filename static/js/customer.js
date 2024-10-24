class CustomerChat {
    constructor() {
        this.chatWidget = document.getElementById('chat-widget');
        this.toggleChat = document.getElementById('toggle-chat');
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.micButton = document.getElementById('mic-button');
        this.micIcon = document.getElementById('mic');
        this.userId = document.body.dataset.userId;

        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];

        // Ensure elements exist
        if (!this.chatWidget || !this.toggleChat || !this.chatMessages || !this.messageInput || !this.sendButton || !this.micButton || !this.micIcon) {
            console.error('One or more elements are missing.');
            return;
        }

        this.socket = io.connect('http://localhost:5000', {
            query: {
                userId: this.userId
            }
        });

        this.toggleChat.addEventListener('click', () => this.toggleChatWidget());
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        this.micButton.addEventListener('click', () => this.toggleRecording());

        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('message', (data) => this.receiveMessage(data));
        this.socket.on('rep_message', (data) => this.receiveRepMessage(data));

        this.loadChatHistory();
    }

    toggleChatWidget() {
        if (this.chatWidget) {
            this.chatWidget.classList.toggle('minimized');
            if (this.chatWidget.classList.contains('minimized')) {
                this.toggleChat.innerHTML = '<i class="fas fa-comments"></i>';
                this.chatWidget.style.height = '60px';
            } else {
                this.toggleChat.innerHTML = '<i class="fas fa-times"></i>';
                this.chatWidget.style.height = '400px';
            }
        } else {
            console.error('Chat widget not found.');
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (message !== '') {
            this.socket.emit('customer_message', { message : message });
            this.addMessageToChat('You', message, 'customer-message');
            this.messageInput.value = '';
        }
    }

    receiveMessage(data) {
        this.addMessageToChat('Representative', data.message, 'rep-message');
    }

    receiveRepMessage(data) {
        this.addMessageToChat('Representative', data.message, 'rep-message');
    }

    addMessageToChat(sender, message, className) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${className}`;
        messageElement.innerHTML = `
            <span class="sender">${sender}</span>
            <span class="content">${this.escapeHtml(message)}</span>
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
        `;
        this.chatMessages.appendChild(messageElement);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    loadChatHistory() {
        fetch('/chat_history')
            .then(response => response.json())
            .then(data => {
                data.forEach(message => {
                    const className = message.is_customer ? 'customer-message' : 'rep-message';
                    const sender = message.is_customer ? 'You' : 'Representative';
                    this.addMessageToChat(sender, message.content, className);
                });
            })
            .catch(error => console.error('Error loading chat history:', error));
    }

    toggleRecording() {
        if (!this.isRecording) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    console.log("Starting recording"); // Debugging line
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.mediaRecorder.start();
                    this.isRecording = true;

                    // Change icon to stop icon
                    this.micIcon.classList.remove('fa-microphone');
                    this.micIcon.classList.add('fa-stop');

                    this.mediaRecorder.ondataavailable = event => {
                        console.log("Data available:", event.data); // Debugging line
                        this.audioChunks.push(event.data);
                    };

                    this.mediaRecorder.onstop = () => {
                        console.log("Stopping recording"); // Debugging line
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                        this.audioChunks = [];

                        // Create FormData to send the file to the server
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recorded_audio.wav');

                        // Send the file to the server
                        fetch('/audio_to_text', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log("File uploaded successfully:", data);
                            // Now you can proceed with text conversion and analysis
                            this.addMessageToChat('You', data.message,'customer-message');
                            this.socket.emit('customer_message', {message : data.message});
                        })
                        .catch(error => {
                            console.error('Error uploading file:', error);
                        });
                    };
                })
                .catch(error => {
                    console.error('Error accessing microphone:', error);
                });
        } else {
            console.log("Stopping recording"); // Debugging line
            this.mediaRecorder.stop();
            this.isRecording = false;

            // Change icon back to mic icon
            this.micIcon.classList.remove('fa-stop');
            this.micIcon.classList.add('fa-microphone');
        }
    }
}

// Instantiate the class after DOM content is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    new CustomerChat();
});
