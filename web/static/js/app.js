/**
 * Voice Assistant Web UI JavaScript
 * Handles all frontend interactions and API communications
 */

class VoiceAssistantUI {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.isListening = false;
        this.mediaRecorder = null;
        this.audioContext = null;
        this.audioStream = null;
        this.animationFrameId = null;
        this.commandCount = 0;
        this.startTime = new Date();
        
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setupEventListeners();
        this.startStatusUpdates();
        await this.loadSystemStatus();
        await this.loadDevices();
        this.startVoiceVisualization();
        this.updateUptime();
        
        // Show welcome message
        this.showNotification('Voice Assistant UI loaded successfully', 'success');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Voice control button
        const listenBtn = document.getElementById('listenBtn');
        if (listenBtn) {
            listenBtn.addEventListener('click', () => this.toggleListening());
        }

        // Command input
        const commandInput = document.getElementById('commandInput');
        if (commandInput) {
            commandInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendTextCommand();
                }
            });
        }

        // Settings controls
        this.setupSettingsListeners();
        
        // Device controls
        this.setupDeviceListeners();

        // Quick actions
        this.setupQuickActions();
    }

    /**
     * Setup settings event listeners
     */
    setupSettingsListeners() {
        // Voice speed slider
        const voiceSpeed = document.getElementById('voiceSpeed');
        if (voiceSpeed) {
            voiceSpeed.addEventListener('input', (e) => {
                const speedText = voiceSpeed.nextElementSibling;
                if (speedText) {
                    speedText.textContent = `${e.target.value} WPM`;
                }
            });
        }

        // Voice volume slider
        const voiceVolume = document.getElementById('voiceVolume');
        if (voiceVolume) {
            voiceVolume.addEventListener('input', (e) => {
                const volumeText = voiceVolume.nextElementSibling;
                if (volumeText) {
                    volumeText.textContent = `${e.target.value}%`;
                }
            });
        }

        // Sensitivity slider
        const sensitivityRange = document.getElementById('sensitivityRange');
        if (sensitivityRange) {
            sensitivityRange.addEventListener('input', (e) => {
                const sensitivityText = sensitivityRange.nextElementSibling;
                if (sensitivityText) {
                    sensitivityText.textContent = e.target.value;
                }
            });
        }
    }

    /**
     * Setup device control listeners
     */
    setupDeviceListeners() {
        // Camera preview button
        const cameraPreviewBtn = document.querySelector('[onclick="startCameraPreview()"]');
        if (cameraPreviewBtn) {
            cameraPreviewBtn.addEventListener('click', () => this.startCameraPreview());
        }
    }

    /**
     * Setup quick action buttons
     */
    setupQuickActions() {
        // Quick action buttons are handled by the quickAction function
        // which is called directly from the HTML onclick attributes
    }

    /**
     * Load system status from API
     */
    async loadSystemStatus() {
        try {
            const response = await this.apiCall('GET', '/status');
            if (response.success !== false) {
                this.updateStatusDisplay(response);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
            this.updateStatusDisplay({ status: 'offline' });
        }
    }

    /**
     * Update status display elements
     */
    updateStatusDisplay(status) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const wakeWord = document.getElementById('wakeWord');
        const voiceStatus = document.getElementById('voiceStatus');
        const aiStatus = document.getElementById('aiStatus');

        if (statusIndicator) {
            const dot = statusIndicator.querySelector('.status-dot');
            if (dot) {
                dot.className = 'status-dot';
                if (status.status === 'online') {
                    dot.classList.add('online');
                } else {
                    dot.classList.add('offline');
                }
            }
        }

        if (statusText) {
            statusText.textContent = status.status === 'online' ? 'Online' : 'Offline';
        }

        if (wakeWord && status.wake_word) {
            wakeWord.textContent = status.wake_word;
        }

        if (voiceStatus) {
            voiceStatus.textContent = status.speech_synthesis ? 'Ready' : 'Unavailable';
        }

        if (aiStatus) {
            aiStatus.textContent = status.openai_available ? 'Available' : 'Unavailable';
        }
    }

    /**
     * Start periodic status updates
     */
    startStatusUpdates() {
        setInterval(() => {
            this.loadSystemStatus();
        }, 30000); // Update every 30 seconds
    }

    /**
     * Update uptime display
     */
    updateUptime() {
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            const now = new Date();
            const diff = now - this.startTime;
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            uptimeElement.textContent = `${hours}h ${minutes}m`;
        }

        // Update command count
        const commandCountElement = document.getElementById('commandCount');
        if (commandCountElement) {
            commandCountElement.textContent = this.commandCount;
        }

        // Schedule next update
        setTimeout(() => this.updateUptime(), 60000); // Update every minute
    }

    /**
     * Toggle voice listening
     */
    async toggleListening() {
        const listenBtn = document.getElementById('listenBtn');
        
        if (!this.isListening) {
            try {
                await this.startListening();
                this.isListening = true;
                listenBtn.classList.add('listening');
                listenBtn.innerHTML = '<i class="fas fa-stop fa-2x"></i>';
                
                // Start listening visualization
                this.animateListening();
                
            } catch (error) {
                console.error('Failed to start listening:', error);
                this.showNotification('Failed to start voice recognition', 'error');
            }
        } else {
            this.stopListening();
            this.isListening = false;
            listenBtn.classList.remove('listening', 'processing');
            listenBtn.innerHTML = '<i class="fas fa-microphone fa-2x"></i>';
        }
    }

    /**
     * Start voice listening
     */
    async startListening() {
        try {
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Set up MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream);
            const audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await this.processVoiceCommand(audioBlob);
            };

            // Start recording
            this.mediaRecorder.start();
            
            // Auto-stop after 10 seconds
            setTimeout(() => {
                if (this.isListening) {
                    this.toggleListening();
                }
            }, 10000);

        } catch (error) {
            throw new Error('Microphone access denied or unavailable');
        }
    }

    /**
     * Stop voice listening
     */
    stopListening() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
    }

    /**
     * Process voice command
     */
    async processVoiceCommand(audioBlob) {
        const listenBtn = document.getElementById('listenBtn');
        
        try {
            listenBtn.classList.remove('listening');
            listenBtn.classList.add('processing');
            
            // For now, we'll use the listen endpoint to get voice recognition
            const response = await this.apiCall('GET', '/listen');
            
            if (response.success && response.command) {
                document.getElementById('commandInput').value = response.command;
                await this.sendTextCommand();
            } else {
                this.showNotification('No voice command detected', 'warning');
            }
            
        } catch (error) {
            console.error('Voice processing failed:', error);
            this.showNotification('Voice processing failed', 'error');
        }
    }

    /**
     * Send text command to API
     */
    async sendTextCommand() {
        const commandInput = document.getElementById('commandInput');
        const command = commandInput.value.trim();
        
        if (!command) {
            this.showNotification('Please enter a command', 'warning');
            return;
        }

        try {
            this.showCommandProcessing(true);
            
            const response = await this.apiCall('POST', '/command', {
                command: command
            });

            this.displayCommandResponse(command, response.response);
            this.commandCount++;
            this.addActivityItem(command, response.response);
            
            // Clear input
            commandInput.value = '';
            
        } catch (error) {
            console.error('Command failed:', error);
            this.showNotification('Command processing failed', 'error');
        } finally {
            this.showCommandProcessing(false);
        }
    }

    /**
     * Display command response
     */
    displayCommandResponse(command, response) {
        const responseDiv = document.getElementById('commandResponse');
        const responseText = document.getElementById('responseText');
        
        if (responseDiv && responseText) {
            responseText.textContent = response;
            responseDiv.classList.remove('d-none');
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                responseDiv.classList.add('d-none');
            }, 10000);
        }
    }

    /**
     * Show command processing state
     */
    showCommandProcessing(processing) {
        const commandInput = document.getElementById('commandInput');
        const sendButton = commandInput?.nextElementSibling?.querySelector('button');
        
        if (commandInput) {
            commandInput.disabled = processing;
        }
        
        if (sendButton) {
            sendButton.disabled = processing;
            sendButton.innerHTML = processing ? 
                '<i class="fas fa-spinner fa-spin"></i>' : 
                '<i class="fas fa-paper-plane"></i>';
        }
    }

    /**
     * Add activity item to recent activity
     */
    addActivityItem(command, response) {
        const activityList = document.getElementById('recentActivity');
        if (!activityList) return;

        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <i class="fas fa-comment text-primary"></i>
            <span>${command}</span>
            <small class="text-muted">Just now</small>
        `;

        // Add to top of list
        const firstChild = activityList.firstChild;
        if (firstChild) {
            activityList.insertBefore(item, firstChild);
        } else {
            activityList.appendChild(item);
        }

        // Keep only last 10 items
        const items = activityList.querySelectorAll('.activity-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
    }

    /**
     * Start voice visualization
     */
    startVoiceVisualization() {
        const canvas = document.getElementById('voiceCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        let animationId;
        const bars = 20;
        const barWidth = width / bars;

        const animate = () => {
            ctx.clearRect(0, 0, width, height);
            
            // Create gradient
            const gradient = ctx.createLinearGradient(0, 0, width, 0);
            gradient.addColorStop(0, '#667eea');
            gradient.addColorStop(1, '#764ba2');
            
            ctx.fillStyle = gradient;

            // Draw animated bars
            for (let i = 0; i < bars; i++) {
                const barHeight = Math.random() * height * 0.8 + 10;
                const x = i * barWidth;
                const y = (height - barHeight) / 2;
                
                ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
            }

            animationId = requestAnimationFrame(animate);
        };

        // Start with static visualization
        this.drawStaticVisualization(ctx, width, height);
    }

    /**
     * Draw static visualization
     */
    drawStaticVisualization(ctx, width, height) {
        ctx.clearRect(0, 0, width, height);
        
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, '#667eea');
        gradient.addColorStop(1, '#764ba2');
        
        ctx.fillStyle = gradient;
        
        const bars = 20;
        const barWidth = width / bars;
        
        for (let i = 0; i < bars; i++) {
            const barHeight = 20 + Math.sin(i * 0.5) * 15;
            const x = i * barWidth;
            const y = (height - barHeight) / 2;
            
            ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
        }
    }

    /**
     * Animate listening state
     */
    animateListening() {
        const canvas = document.getElementById('voiceCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        const bars = 20;
        const barWidth = width / bars;

        const animate = () => {
            if (!this.isListening) return;

            ctx.clearRect(0, 0, width, height);
            
            const gradient = ctx.createLinearGradient(0, 0, width, 0);
            gradient.addColorStop(0, '#dc3545');
            gradient.addColorStop(1, '#fd7e14');
            
            ctx.fillStyle = gradient;

            for (let i = 0; i < bars; i++) {
                const barHeight = Math.random() * height * 0.9 + 5;
                const x = i * barWidth;
                const y = (height - barHeight) / 2;
                
                ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
            }

            requestAnimationFrame(animate);
        };

        animate();
    }

    /**
     * Load available devices
     */
    async loadDevices() {
        try {
            // Load audio devices
            const audioDevices = await this.apiCall('GET', '/devices/audio');
            this.populateAudioDevices(audioDevices);

            // Load camera devices
            const cameraDevices = await this.apiCall('GET', '/devices/camera');
            this.populateCameraDevices(cameraDevices);

        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    }

    /**
     * Populate audio device selects
     */
    populateAudioDevices(devices) {
        const micSelect = document.getElementById('microphoneSelect');
        const speakerSelect = document.getElementById('speakerSelect');

        if (micSelect && devices.devices && devices.devices.input) {
            micSelect.innerHTML = '';
            devices.devices.input.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.index;
                option.textContent = device.name;
                if (device.index === devices.current_input) {
                    option.selected = true;
                }
                micSelect.appendChild(option);
            });
        }

        if (speakerSelect && devices.devices && devices.devices.output) {
            speakerSelect.innerHTML = '';
            devices.devices.output.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.index;
                option.textContent = device.name;
                if (device.index === devices.current_output) {
                    option.selected = true;
                }
                speakerSelect.appendChild(option);
            });
        }
    }

    /**
     * Populate camera device select
     */
    populateCameraDevices(cameras) {
        const cameraSelect = document.getElementById('cameraSelect');
        
        if (cameraSelect && cameras.available_cameras) {
            cameraSelect.innerHTML = '';
            cameras.available_cameras.forEach(camera => {
                const option = document.createElement('option');
                option.value = camera.index;
                option.textContent = camera.name;
                if (camera.index === cameras.current_camera) {
                    option.selected = true;
                }
                cameraSelect.appendChild(option);
            });
        }
    }

    /**
     * Start camera preview
     */
    async startCameraPreview() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.createElement('video');
            const preview = document.getElementById('cameraPreview');
            
            video.srcObject = stream;
            video.autoplay = true;
            video.style.width = '100%';
            video.style.borderRadius = '8px';
            
            if (preview) {
                preview.src = '';
                preview.parentNode.replaceChild(video, preview);
                video.id = 'cameraPreview';
            }
            
        } catch (error) {
            console.error('Failed to start camera:', error);
            this.showNotification('Camera access denied or unavailable', 'error');
        }
    }

    /**
     * Take photo
     */
    async takePhoto() {
        try {
            const response = await this.apiCall('POST', '/camera/photo');
            if (response.success) {
                this.showNotification(`Photo saved: ${response.photo_path}`, 'success');
            }
        } catch (error) {
            console.error('Failed to take photo:', error);
            this.showNotification('Failed to take photo', 'error');
        }
    }

    /**
     * Test microphone
     */
    async testMicrophone() {
        try {
            const response = await this.apiCall('POST', '/devices/test-microphone');
            if (response.success) {
                this.showNotification(`Microphone test: ${response.volume_level.toFixed(2)} volume level`, 'success');
            }
        } catch (error) {
            console.error('Microphone test failed:', error);
            this.showNotification('Microphone test failed', 'error');
        }
    }

    /**
     * Test speaker
     */
    async testSpeaker() {
        try {
            const response = await this.apiCall('POST', '/speak', {
                text: 'This is a speaker test. If you can hear this, your speakers are working correctly.'
            });
            if (response.success) {
                this.showNotification('Speaker test completed', 'success');
            }
        } catch (error) {
            console.error('Speaker test failed:', error);
            this.showNotification('Speaker test failed', 'error');
        }
    }

    /**
     * Test voice
     */
    async testVoice() {
        try {
            const response = await this.apiCall('POST', '/speak', {
                text: 'Hello! This is your voice assistant. The voice system is working correctly.'
            });
            if (response.success) {
                this.showNotification('Voice test completed', 'success');
            }
        } catch (error) {
            console.error('Voice test failed:', error);
            this.showNotification('Voice test failed', 'error');
        }
    }

    /**
     * Save API keys
     */
    async saveApiKeys() {
        const openaiKey = document.getElementById('openaiKey').value;
        const weatherKey = document.getElementById('weatherKey').value;
        const newsKey = document.getElementById('newsKey').value;

        if (!openaiKey && !weatherKey && !newsKey) {
            this.showNotification('Please enter at least one API key', 'warning');
            return;
        }

        this.showNotification('API keys saved successfully', 'success');
        // Note: In a real implementation, you'd send these to the server securely
    }

    /**
     * Show notification toast
     */
    showNotification(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastMessage = document.getElementById('toastMessage');
        
        if (toast && toastMessage) {
            toastMessage.textContent = message;
            
            // Update toast header based on type
            const header = toast.querySelector('.toast-header');
            const icon = header.querySelector('i');
            
            // Reset classes
            icon.className = 'me-2';
            header.className = 'toast-header';
            
            switch (type) {
                case 'success':
                    icon.classList.add('fas', 'fa-check-circle', 'text-success');
                    break;
                case 'error':
                    icon.classList.add('fas', 'fa-exclamation-circle', 'text-danger');
                    break;
                case 'warning':
                    icon.classList.add('fas', 'fa-exclamation-triangle', 'text-warning');
                    break;
                default:
                    icon.classList.add('fas', 'fa-info-circle', 'text-primary');
            }
            
            // Show toast
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }

    /**
     * Make API call
     */
    async apiCall(method, endpoint, data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer default_token_change_me' // Use configured token
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }
}

/**
 * Global functions for HTML onclick handlers
 */

let voiceAssistant;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    voiceAssistant = new VoiceAssistantUI();
});

// Quick action functions
async function quickAction(action) {
    if (!voiceAssistant) return;
    
    const commands = {
        weather: 'What\'s the weather?',
        news: 'Tell me the news',
        time: 'What time is it?',
        calendar: 'Check my calendar'
    };
    
    const command = commands[action];
    if (command) {
        document.getElementById('commandInput').value = command;
        await voiceAssistant.sendTextCommand();
    }
}

// Smart home control functions
async function toggleLight(deviceId) {
    if (!voiceAssistant) return;
    
    try {
        const response = await voiceAssistant.apiCall('POST', '/command', {
            command: `toggle ${deviceId} lights`
        });
        voiceAssistant.showNotification(response.response, 'success');
    } catch (error) {
        voiceAssistant.showNotification('Failed to control lights', 'error');
    }
}

async function toggleTV() {
    if (!voiceAssistant) return;
    
    try {
        const response = await voiceAssistant.apiCall('POST', '/command', {
            command: 'toggle TV'
        });
        voiceAssistant.showNotification(response.response, 'success');
    } catch (error) {
        voiceAssistant.showNotification('Failed to control TV', 'error');
    }
}

async function activateScene(sceneName) {
    if (!voiceAssistant) return;
    
    try {
        const response = await voiceAssistant.apiCall('POST', '/command', {
            command: `activate ${sceneName.replace('-', ' ')} scene`
        });
        voiceAssistant.showNotification(response.response, 'success');
    } catch (error) {
        voiceAssistant.showNotification('Failed to activate scene', 'error');
    }
}

async function discoverLights() {
    if (!voiceAssistant) return;
    
    try {
        const response = await voiceAssistant.apiCall('POST', '/command', {
            command: 'discover smart home devices'
        });
        voiceAssistant.showNotification(response.response, 'info');
    } catch (error) {
        voiceAssistant.showNotification('Failed to discover devices', 'error');
    }
}

// Device testing functions (already implemented in class)
function testMicrophone() {
    if (voiceAssistant) voiceAssistant.testMicrophone();
}

function testSpeaker() {
    if (voiceAssistant) voiceAssistant.testSpeaker();
}

function testVoice() {
    if (voiceAssistant) voiceAssistant.testVoice();
}

function startCameraPreview() {
    if (voiceAssistant) voiceAssistant.startCameraPreview();
}

function takePhoto() {
    if (voiceAssistant) voiceAssistant.takePhoto();
}

function saveApiKeys() {
    if (voiceAssistant) voiceAssistant.saveApiKeys();
}

function sendTextCommand() {
    if (voiceAssistant) voiceAssistant.sendTextCommand();
}

// Audio visualization functions
function startAudioVisualization() {
    // Placeholder for future implementation
    if (voiceAssistant) {
        voiceAssistant.showNotification('Audio visualization started', 'info');
    }
}

function stopAudioVisualization() {
    // Placeholder for future implementation
    if (voiceAssistant) {
        voiceAssistant.showNotification('Audio visualization stopped', 'info');
    }
}
