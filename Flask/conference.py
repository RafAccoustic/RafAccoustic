# First, import and initialize eventlet at the very top
import eventlet

eventlet.monkey_patch()
# Then import other modules
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import cv2
import numpy as np
import base64
import uuid
import pyaudio
import threading
import time
import os

# Store active rooms and participants
rooms = {}

# Audio stream configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Configure Socket.IO with improved payload settings
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    max_http_buffer_size=5 * 1024 * 1024,  # Reduce to 5MB
    ping_timeout=60,
    ping_interval=25,
    async_mode='eventlet'  # Use eventlet for better performance
)


# Routes
@app.route('/')
def index():
    """Landing page with room creation option"""
    return render_template('index.html')


@app.route('/room/<room_id>')
def room(room_id):
    """Video conference room page"""
    if room_id not in rooms:
        rooms[room_id] = {"participants": {}}

    # Generate a unique ID for this participant
    participant_id = str(uuid.uuid4())
    session['participant_id'] = participant_id
    session['room_id'] = room_id

    return render_template('room.html', room_id=room_id, participant_id=participant_id)


# Socket.IO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')


@socketio.on('join')
def handle_join(data):
    """Handle a participant joining a room"""
    room_id = data['room_id']
    participant_id = data['participant_id']
    username = data.get('username', f"User-{participant_id[:5]}")

    if room_id not in rooms:
        rooms[room_id] = {"participants": {}}

    # Add participant to room
    rooms[room_id]["participants"][participant_id] = {
        "username": username,
        "joined_at": time.time()
    }

    join_room(room_id)

    # Notify others in the room
    emit('user_joined', {
        'participant_id': participant_id,
        'username': username,
        'participant_count': len(rooms[room_id]["participants"])
    }, room=room_id)

    print(f"{username} joined room {room_id}")


@socketio.on('leave')
def handle_leave(data):
    """Handle a participant leaving a room"""
    room_id = data['room_id']
    participant_id = data['participant_id']

    if room_id in rooms and participant_id in rooms[room_id]["participants"]:
        username = rooms[room_id]["participants"][participant_id]["username"]
        del rooms[room_id]["participants"][participant_id]

        # Remove room if empty
        if len(rooms[room_id]["participants"]) == 0:
            del rooms[room_id]

        leave_room(room_id)

        # Notify others in the room
        emit('user_left', {
            'participant_id': participant_id,
            'username': username,
            'participant_count': len(rooms[room_id]["participants"]) if room_id in rooms else 0
        }, room=room_id)

        print(f"{username} left room {room_id}")


@socketio.on('video_frame')
def handle_video_frame(data):
    """Handle incoming video frames and broadcast to room participants"""
    room_id = data['room_id']
    participant_id = data['participant_id']
    frame_data = data['frame']

    # Broadcast to all other participants in the room
    emit('video_frame', {
        'participant_id': participant_id,
        'frame': frame_data
    }, room=room_id, include_self=False)


@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle incoming audio data and broadcast to room participants"""
    room_id = data['room_id']
    participant_id = data['participant_id']
    audio_data = data['audio']
    audio_format = data.get('format', 'pcm')  # Default to pcm for backward compatibility

    # Broadcast to all other participants in the room
    emit('audio_data', {
        'participant_id': participant_id,
        'audio': audio_data,
        'format': audio_format
    }, room=room_id, include_self=False)


@socketio.on('audio_activity')
def handle_audio_activity(data):
    """Handle audio activity status and broadcast to room participants"""
    room_id = data['room_id']
    participant_id = data['participant_id']
    is_speaking = data['is_speaking']

    # Broadcast to all other participants in the room
    emit('audio_activity', {
        'participant_id': participant_id,
        'is_speaking': is_speaking
    }, room=room_id, include_self=False)


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages and broadcast to room participants"""
    room_id = data['room_id']
    participant_id = data['participant_id']
    message = data['message']

    if room_id in rooms and participant_id in rooms[room_id]["participants"]:
        username = rooms[room_id]["participants"][participant_id]["username"]

        # Broadcast the message to all participants in the room
        emit('chat_message', {
            'participant_id': participant_id,
            'username': username,
            'message': message,
            'timestamp': time.time()
        }, room=room_id)


# Run the application
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Create basic HTML templates
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Python Video Conference App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { text-align: center; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        input { padding: 10px; font-size: 16px; width: 300px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Python Video Conference App</h1>
        <div>
            <input type="text" id="username" placeholder="Your Name" />
            <button onclick="createRoom()">Create New Meeting</button>
        </div>
        <div style="margin-top: 20px;">
            <input type="text" id="roomId" placeholder="Meeting ID" />
            <button onclick="joinRoom()">Join Meeting</button>
        </div>
    </div>

    <script>
        function createRoom() {
            const roomId = Math.random().toString(36).substring(2, 8);
            const username = document.getElementById('username').value || 'Anonymous';
            window.location.href = `/room/${roomId}?username=${encodeURIComponent(username)}`;
        }

        function joinRoom() {
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value || 'Anonymous';
            if (roomId) {
                window.location.href = `/room/${roomId}?username=${encodeURIComponent(username)}`;
            } else {
                alert('Please enter a Meeting ID');
            }
        }
    </script>
</body>
</html>
        ''')

    with open('templates/room.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Meeting Room</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .container { display: flex; height: 100vh; }
        .video-container { flex: 1; display: flex; flex-wrap: wrap; }
        .video-box { position: relative; width: 320px; height: 240px; margin: 5px; background: #000; }
        video { width: 100%; height: 100%; }
        .participant-name { position: absolute; bottom: 5px; left: 5px; color: white; background: rgba(0,0,0,0.5); padding: 3px; }
        .controls { position: fixed; bottom: 20px; left: 0; right: 0; text-align: center; }
        .controls button { margin: 0 10px; padding: 10px 20px; }
        .chat-container { width: 300px; border-left: 1px solid #ccc; display: flex; flex-direction: column; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 10px; }
        .chat-input { display: flex; padding: 10px; border-top: 1px solid #ccc; }
        .chat-input input { flex: 1; padding: 5px; }
        .chat-input button { margin-left: 10px; }
        .message { margin-bottom: 10px; }
        .message .sender { font-weight: bold; }

        /* Audio indicator styles */
        .audio-indicator {
            position: absolute;
            top: 5px;
            right: 5px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ccc;
            opacity: 0.7;
        }

        .audio-indicator.active {
            background-color: #2ecc71;
            color: white;
            animation: pulse 1s infinite alternate;
        }

        @keyframes pulse {
            0% {
                opacity: 0.7;
                transform: scale(1);
            }
            100% {
                opacity: 1;
                transform: scale(1.1);
            }
        }

        /* Make sure we have room for the icon */
        @media (max-width: 768px) {
            .video-box {
                position: relative;
                width: 160px;
                height: 120px;
            }

            .audio-indicator {
                width: 20px;
                height: 20px;
                font-size: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="video-container" id="videoContainer">
            <div class="video-box">
                <video id="localVideo" autoplay muted></video>
                <div class="participant-name">You</div>
            </div>
        </div>
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Type a message..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <div class="controls">
        <button id="toggleVideo" onclick="toggleVideo()">Video Off</button>
        <button id="toggleAudio" onclick="toggleAudio()">Mute</button>
        <button id="shareScreen" onclick="toggleScreenShare()">Share Screen</button>
        <button id="leaveBtn" onclick="leaveRoom()">Leave Meeting</button>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        // Meeting configuration
        const roomId = '{{ room_id }}';
        const participantId = '{{ participant_id }}';
        const username = new URLSearchParams(window.location.search).get('username') || 'Anonymous';

        // Connection state
        let socket;
        let localStream;
        let screenStream;
        let isVideoOn = true;
        let isAudioOn = true;
        let isScreenSharing = false;

        // Audio context
        let audioContext;

        // For frame rate control and compression
        let frameInterval = 200; // Send a frame every 200ms (5 FPS)
        let jpegQuality = 0.3; // JPEG compression quality (0.1 - 1.0)

        // For audio sampling
        let audioSendInterval = 200; // Send audio every 200ms

        // Initialize the room
        window.onload = async function() {
            try {
                // Get user media
                localStream = await navigator.mediaDevices.getUserMedia({ 
                    video: {
                        width: { ideal: 320 },
                        height: { ideal: 240 },
                        frameRate: { ideal: 15 }
                    }, 
                    audio: true 
                });
                document.getElementById('localVideo').srcObject = localStream;

                // Configure socket.io
                socket = io({
                    transports: ['websocket'],  // Force WebSocket transport
                    upgrade: false,             // Disable transport upgrade
                    reconnection: true,         // Enable reconnection
                    reconnectionAttempts: 5,    // Try to reconnect 5 times
                    reconnectionDelay: 1000,    // Start with 1s delay
                    timeout: 20000              // Increase timeout
                });

                // Join the room
                socket.on('connect', function() {
                    console.log("Connected to server");
                    socket.emit('join', { room_id: roomId, participant_id: participantId, username: username });
                });

                // Handle connection errors
                socket.on('connect_error', function(error) {
                    console.error("Connection error:", error);
                    alert("Connection error: " + error);
                });

                // Handle new participant joining
                socket.on('user_joined', function(data) {
                    console.log('User joined:', data);
                    // You would add logic to create a new video element for this participant
                    addParticipantVideo(data.participant_id, data.username);
                });

                // Handle participant leaving
                socket.on('user_left', function(data) {
                    console.log('User left:', data);
                    // Remove the participant's video
                    removeParticipantVideo(data.participant_id);
                });

                // Handle incoming video frames
                socket.on('video_frame', function(data) {
                    updateParticipantVideo(data.participant_id, data.frame);
                });

                // Replace the existing audio_data handler with this one
                socket.on('audio_data', function(data) {
                    try {
                        // Check the format
                        const format = data.format || 'pcm';

                        if (format === 'webm') {
                            // For webm format
                            const binary = atob(data.audio);
                            const bytes = new Uint8Array(binary.length);
                            for (let i = 0; i < binary.length; i++) {
                                bytes[i] = binary.charCodeAt(i);
                            }

                            // Create a blob and play it
                            const blob = new Blob([bytes], { type: 'audio/webm;codecs=opus' });
                            const url = URL.createObjectURL(blob);
                            const audio = new Audio(url);
                            audio.play();

                            // Clean up URL object when done
                            audio.onended = () => {
                                URL.revokeObjectURL(url);
                            };
                        } else {
                            // Original PCM format processing
                            // Create audioContext if it doesn't exist yet
                            if (!audioContext) {
                                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            }

                            // Decode base64
                            const binary = atob(data.audio);
                            const bytes = new Uint8Array(binary.length);
                            for (let i = 0; i < binary.length; i++) {
                                bytes[i] = binary.charCodeAt(i);
                            }

                            // Convert from Int16 to Float32
                            const floatArray = new Float32Array(bytes.length/2);
                            for (let i = 0; i < bytes.length/2; i++) {
                                // Convert from Int16 to float
                                const int16 = (bytes[i*2] | (bytes[i*2+1] << 8));
                                // Handle two's complement
                                const adjusted = int16 >= 0x8000 ? int16 - 0x10000 : int16;
                                floatArray[i] = adjusted / 0x7FFF;
                            }

                            // Create a buffer
                            const buffer = audioContext.createBuffer(1, floatArray.length, 44100);
                            buffer.getChannelData(0).set(floatArray);

                            // Play the audio
                            const source = audioContext.createBufferSource();
                            source.buffer = buffer;
                            source.connect(audioContext.destination);
                            source.start();
                        }
                    } catch (e) {
                        console.error("Audio processing error:", e);
                    }
                });
                // Handle audio activity indicators
                socket.on('audio_activity', function(data) {
                    const participantId = data.participant_id;
                    const isSpeaking = data.is_speaking;

                    // Find the participant's video container
                    const container = document.getElementById(`container-${participantId}`);
                    if (!container) return;

                    // Find or create audio indicator
                    let audioIndicator = container.querySelector('.audio-indicator');
                    if (!audioIndicator) {
                        audioIndicator = document.createElement('div');
                        audioIndicator.className = 'audio-indicator';
                        audioIndicator.innerHTML = '<i class="fas fa-microphone"></i>';
                        container.appendChild(audioIndicator);
                    }

                    // Update the indicator
                    if (isSpeaking) {
                        audioIndicator.classList.add('active');
                    } else {
                        audioIndicator.classList.remove('active');
                    }
                });

                // Handle chat messages
                socket.on('chat_message', function(data) {
                    addChatMessage(data.username, data.message);
                });

                // Start sending video frames
                startVideoTransmission();

                // Start audio transmission with indicators
                startAudioTransmission();

            } catch (error) {
                console.error('Error initializing:', error);
                alert('Could not access camera or microphone. Please check permissions.');
            }
        };

        // Video transmission with rate limiting and compression
        function startVideoTransmission() {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            const video = document.getElementById('localVideo');

            canvas.width = 320;
            canvas.height = 240;

            // Use setInterval for consistent frame rate
            setInterval(() => {
                if (isVideoOn && localStream && localStream.getVideoTracks()[0].enabled) {
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    // Get compressed JPEG data
                    const frame = canvas.toDataURL('image/jpeg', jpegQuality);

                    // Only send if socket is connected
                    if (socket && socket.connected) {
                        socket.emit('video_frame', {
                            room_id: roomId,
                            participant_id: participantId,
                            frame: frame
                        });
                    }
                }
            }, frameInterval);
        }

        // Audio transmission with level detection and rate limiting
        function startAudioTransmission() {
            if (!localStream) return;

            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(localStream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;

            source.connect(analyser);

            // For audio processing
            const processor = audioContext.createScriptProcessor(1024, 1, 1);
            analyser.connect(processor);
            processor.connect(audioContext.destination);

            // For audio level detection
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            // Control the rate of transmission
            let lastSendTime = 0;

            // Create audio level indicator for local video
            const localVideoContainer = document.getElementById('localVideo').parentElement;
            const localAudioIndicator = document.createElement('div');
            localAudioIndicator.className = 'audio-indicator';
            localAudioIndicator.innerHTML = '<i class="fas fa-microphone"></i>';
            localVideoContainer.appendChild(localAudioIndicator);

            // Function to update audio indicators
            function updateAudioIndicator(level) {
                // Threshold for "speaking" - adjust as needed
                const SPEAKING_THRESHOLD = 30;
                const isSpeaking = level > SPEAKING_THRESHOLD;

                if (isSpeaking) {
                    localAudioIndicator.classList.add('active');

                    // Only send this occasionally to reduce traffic
                    if (Date.now() - lastSendTime > 500) {
                        // Send audio activity status to others
                        if (socket && socket.connected) {
                            socket.emit('audio_activity', {
                                room_id: roomId,
                                participant_id: participantId,
                                is_speaking: true
                            });
                            lastSendTime = Date.now();
                        }
                    }
                } else {
                    localAudioIndicator.classList.remove('active');

                    // Only send this occasionally to reduce traffic
                    if (Date.now() - lastSendTime > 500) {
                        // Send audio inactivity
                        if (socket && socket.connected) {
                            socket.emit('audio_activity', {
                                room_id: roomId,
                                participant_id: participantId,
                                is_speaking: false
                            });
                            lastSendTime = Date.now();
                        }
                    }
                }

                return isSpeaking;
            }

            // Audio processing for level detection
            processor.onaudioprocess = function(e) {
                // Get current audio levels for activity indicator
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for(let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                const average = sum / bufferLength;
                updateAudioIndicator(average);
            };

            // Separate interval for sending audio data less frequently
            setInterval(() => {
                if (isAudioOn && localStream && localStream.getAudioTracks()[0].enabled) {
                    // Skip if socket is not connected
                    if (!socket || !socket.connected) return;

                    // Get audio data from microphone
                    const audioTrack = localStream.getAudioTracks()[0];
                    const audioProcessor = new AudioContext();
                    const source = audioProcessor.createMediaStreamSource(new MediaStream([audioTrack]));
                    const destination = audioProcessor.createMediaStreamDestination();

                    // Create a script processor node for getting raw audio data
                    const scriptNode = audioProcessor.createScriptProcessor(256, 1, 1);
                    source.connect(scriptNode);
                    scriptNode.connect(destination);

                    // One-time processing to get a sample
                    scriptNode.onaudioprocess = function(e) {
                        // Get just a small chunk of audio data
                        const inputBuffer = e.inputBuffer;
                        const inputData = inputBuffer.getChannelData(0);

                        // Convert to 16-bit PCM (smaller data size)
                        const pcmData = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {
                            pcmData[i] = inputData[i] * 0x7FFF;
                        }

                        // Convert to base64
                        const base64data = btoa(String.fromCharCode.apply(null, 
                            new Uint8Array(pcmData.buffer)));

                        // Send the data
                        socket.emit('audio_data', {
                            room_id: roomId,
                            participant_id: participantId,
                            audio: base64data
                        });

                        // Clean up
                        source.disconnect();
                        scriptNode.disconnect();
                    };
                }
            }, audioSendInterval);
        }

        // UI Functions
        function toggleVideo() {
            isVideoOn = !isVideoOn;
            localStream.getVideoTracks().forEach(track => track.enabled = isVideoOn);
            document.getElementById('toggleVideo').textContent = isVideoOn ? 'Video Off' : 'Video On';
        }

        function toggleAudio() {
            isAudioOn = !isAudioOn;
            localStream.getAudioTracks().forEach(track => track.enabled = isAudioOn);
            document.getElementById('toggleAudio').textContent = isAudioOn ? 'Mute' : 'Unmute';
        }

        async function toggleScreenShare() {
            if (!isScreenSharing) {
                try {
                    screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                    const videoTrack = screenStream.getVideoTracks()[0];

                    // Just display the screen share locally
                    document.getElementById('localVideo').srcObject = screenStream;
                    document.getElementById('shareScreen').textContent = 'Stop Sharing';
                    isScreenSharing = true;

                    // Listen for the end of screen sharing
                    videoTrack.onended = () => {
                        stopScreenSharing();
                    };
                } catch (error) {
                    console.error('Error sharing screen:', error);
                }
            } else {
                stopScreenSharing();
            }
        }

        function stopScreenSharing() {
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
                document.getElementById('localVideo').srcObject = localStream;
                document.getElementById('shareScreen').textContent = 'Share Screen';
                isScreenSharing = false;
            }
        }

        function leaveRoom() {
            socket.emit('leave', { room_id: roomId, participant_id: participantId });

            // Stop all tracks
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
            }

            // Disconnect socket
            socket.disconnect();

            // Redirect to home
            window.location.href = '/';
        }

        function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();

            if (message) {
                socket.emit('chat_message', {
                    room_id: roomId,
                    participant_id: participantId,
                    message: message
                });

                // Add to local chat
                addChatMessage('You', message);

                // Clear input
                messageInput.value = '';
            }
        }

        // Helper functions for UI updates
        function addParticipantVideo(participantId, username) {
            const videoContainer = document.getElementById('videoContainer');

            // Create video element if it doesn't exist
            if (!document.getElementById(`video-${participantId}`)) {
                const videoBox = document.createElement('div');
                videoBox.className = 'video-box';
                videoBox.id = `container-${participantId}`;

                const video = document.createElement('video');
                video.id = `video-${participantId}`;
                video.autoplay = true;

                const nameLabel = document.createElement('div');
                nameLabel.className = 'participant-name';
                nameLabel.textContent = username;

                // Add audio indicator
                const audioIndicator = document.createElement('div');
                audioIndicator.className = 'audio-indicator';
                audioIndicator.innerHTML = '<i class="fas fa-microphone"></i>';

                videoBox.appendChild(video);
                videoBox.appendChild(nameLabel);
                videoBox.appendChild(audioIndicator);
                videoContainer.appendChild(videoBox);
            }
        }

        function removeParticipantVideo(participantId) {
            const container = document.getElementById(`container-${participantId}`);
            if (container) {
                container.remove();
            }
        }

        function updateParticipantVideo(participantId, frame) {
            const video = document.getElementById(`video-${participantId}`);
            if (video) {
                // Just set the image directly to the video src
                video.src = frame;
            }
        }

        function addChatMessage(sender, message) {
            const chatMessages = document.getElementById('chatMessages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message';

            const senderElement = document.createElement('div');
            senderElement.className = 'sender';
            senderElement.textContent = sender;

            const contentElement = document.createElement('div');
            contentElement.className = 'content';
            contentElement.textContent = message;

            messageElement.appendChild(senderElement);
            messageElement.appendChild(contentElement);
            chatMessages.appendChild(messageElement);

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Add event listener for Enter key in chat
        document.getElementById('messageInput').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
        ''')

    print("Starting video conferencing server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)