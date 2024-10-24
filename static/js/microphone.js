const micButton = document.getElementById('mic-button');
const micIcon = document.getElementById('mic');
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Check if the browser supports the Web Audio API
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    micButton.addEventListener('click', () => {
        console.log("Mic button clicked"); // Debugging line
        if (!isRecording) {
            // Start recording
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    console.log("Starting recording"); // Debugging line
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    isRecording = true;

                    // Change icon to stop icon
                    micIcon.classList.remove('fa-microphone');
                    micIcon.classList.add('fa-stop');

                    mediaRecorder.ondataavailable = event => {
                        console.log("Data available:", event.data); // Debugging line
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        console.log("Stopping recording"); // Debugging line
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        audioChunks = [];

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


                            // fetching the conversation
                            // sendMessage(data.message)
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
            // Stop recording
            console.log("Stopping recording"); // Debugging line
            mediaRecorder.stop();
            isRecording = false;

            // Change icon back to mic icon
            micIcon.classList.remove('fa-stop');
            micIcon.classList.add('fa-microphone');
        }
    });
} else {
    console.error('getUserMedia is not supported in this browser.');
}
