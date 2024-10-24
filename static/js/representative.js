class RepresentativeChat {
    constructor() {
        this.customerList = document.getElementById('customer-list');
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.summary = document.getElementById('summary');
        this.sentiment = document.getElementById('sentiment');
        this.loanType = document.getElementById('loan-type');
        this.leadType = document.getElementById('lead-type');
        this.rationale = document.getElementById('rationale');
        this.activeSummary = document.getElementById('active-summary');
        this.micButton = document.getElementById('mic-button');
        this.micIcon = document.getElementById('mic');
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.userId = document.body.dataset.userId;
        // this.selectedCustomerName = null;
        this.selectedCustomerId = null;

        console.log('User ID:', this.userId); // Debugging line

        // Connect to the Socket.IO server
        this.socket = io.connect('http://' + document.domain + ':' + location.port, {
            query: { userId: this.userId }
        });

        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        this.micButton.addEventListener('click', () => this.toggleRecording());

        this.socket.on('customer_message', (data) => this.receiveMessage(data));

        this.loadCustomers();
    }

    toggleRecording() {
        if (!this.isRecording) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    console.log("Starting recording"); // Debugging line
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.mediaRecorder.start();
                    this.isRecording = true;

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

                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recorded_audio.wav');

                        fetch('/audio_to_text', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log("File uploaded successfully:", data);
                            this.sendMessage(data.message);  // Use the transcribed message for sending
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

            this.micIcon.classList.remove('fa-stop');
            this.micIcon.classList.add('fa-microphone');
        }
    }

    sendMessage(message = null) {
        const msg = message || this.messageInput.value.trim();
        // if (msg !== '' && this.selectedCustomerName) {
        if (msg !== '') {
            this.socket.emit('rep_message', { message: msg, customer_id : this.selectedCustomerId  });
            this.addMessageToChat('You', msg, 'rep-message');
            this.messageInput.value = '';

            this.analyzeMessage(msg);
        }
    }

    receiveMessage(data) {
        this.addMessageToChat('Customer', data.message, 'customer-message');
        this.analyzeMessage(data.message);
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

    analyzeMessage(currentMessage) {
        const messages = this.chatMessages.querySelectorAll('.message .content');
        let conversationTranscript = '';
        
        messages.forEach((msg) => {
            conversationTranscript += msg.textContent + '\n';
        });

        conversationTranscript += currentMessage;

        console.log("Sending conversation transcript for analysis:", conversationTranscript);  // Debugging line
        
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: conversationTranscript }),
        })
        .then(response => response.json())
        .then(data => {
            console.log("Analysis data received:", data);  // Debugging line
            this.updateAnalysis(data);
        })
        .catch(error => console.error('Error analyzing message:', error));
    }

    updateAnalysis(data) {
        console.log(data);
        this.summary.textContent = data.summary;
        this.sentiment.textContent = data.sentiment;
        this.loanType.textContent = data.loan_type;
        this.leadType.textContent = data.lead_type;
        this.rationale.textContent = data.rationale;
        this.activeSummary.textContent = data.active_summary;
    }

    loadCustomers() {
        fetch('/get_customers')
            .then(response => response.json())
            .then(data => {
                if (Array.isArray(data)) {
                    this.customerList.innerHTML = '';
                    data.forEach(customer => {
                        const li = document.createElement('li');
                        li.textContent = customer.username;
                        li.dataset.customerId = customer.id;
                        li.addEventListener('click', () => this.loadCustomerChat(customer.id));
                        this.customerList.appendChild(li);
                    });
                } else {
                    console.error('Unexpected data format:', data);
                }
            })
            .catch(error => console.error('Error loading customers:', error));
    }

    // customerName --> able to send message from cust to

    loadCustomerChat(customerId) {
        this.selectedCustomerId = customerId
        fetch(`/get_customer/${customerId}`)
            .then(response => response.json())
            .then(data => {
                this.chatMessages.innerHTML = '';
                data.forEach(message => {
                    const className = message.is_customer ? 'customer-message' : 'rep-message';
                    const sender = message.is_customer ? 'Customer' : 'You';
                    this.addMessageToChat(sender, message.content, className);
                });
                document.getElementById('customer-name').textContent = `Chatting with Customer ${customerId}`;
            })
            .catch(error => {
                console.error('Error loading customer chat:', error);
            });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const chat = new RepresentativeChat();
});

setInterval(function() {
    fetch('/check_session')
    .then(response => response.json())
    .then(data => {
        if (!data.is_authenticated || data.role !== 'representative') {
            window.location.href = '/login';
        }
    })
    .catch(error => console.log("Some error occurred", error));
}, 5000); // Check every 5 seconds.
