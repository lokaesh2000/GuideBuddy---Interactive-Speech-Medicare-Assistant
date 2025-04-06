"""
GuideAI Application Settings
Contains configuration settings and initialization functions
"""

import os
import json
from pathlib import Path

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PATIENTS_DIR = os.path.join(DATA_DIR, "patients")
DOCTORS_DIR = os.path.join(DATA_DIR, "doctors")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "credentials.json")

# Ensure all directories exist
def initialize_app_directories():
    """Initialize all required application directories"""
    directories = [
        DATA_DIR,
        PATIENTS_DIR,
        DOCTORS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Initialize credentials file if it doesn't exist
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump({"patients": {}, "doctors": {}}, f)

# Audio settings
AUDIO_SETTINGS = {
    "channels": 1,
    "rate": 16000,
    "chunk": 1024,
    "format": 8,  # For PyAudio.paInt16
    "silence_threshold": 300,
    "silence_duration": 1.0,  # seconds
}

# Whisper model settings
WHISPER_SETTINGS = {
    "model_path": os.path.join(BASE_DIR, "models", "whisper"),
    "model_size": "base",
    "device": "cpu",  # "cuda" for GPU if available
}

# LLM settings
LLM_SETTINGS = {
    "model": "gemini-2.0-flash-thinking-exp-01-21",  # Updated from "gemini-pro" to "gemini-1.0-pro"
    "api_key_file": os.path.join(BASE_DIR, "config", "api_keys.json"),
    "max_tokens": 1024,
    "temperature": 0.7,
}

# Elevenlabs TTS settings
TTS_SETTINGS = {
    "api_key_file": os.path.join(BASE_DIR, "config", "api_keys.json"),
    "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Default voice
}

# UI settings
UI_SETTINGS = {
    "theme": "clam",
    "primary_color": "#4a86e8",
    "secondary_color": "#f0f0f0",
    "text_color": "#333333",
    "font_family": "Arial",
    "header_font_size": 16,
    "normal_font_size": 11,
}

# Get user directory path
def get_user_dir(username, user_type):
    """Get the directory path for a specific user"""
    if user_type.lower() == "patient":
        return os.path.join(PATIENTS_DIR, username)
    elif user_type.lower() == "doctor":
        return os.path.join(DOCTORS_DIR, username)
    else:
        raise ValueError(f"Invalid user type: {user_type}")

# Create user directory if it doesn't exist
def create_user_dir(username, user_type):
    """Create directory structure for a new user"""
    user_dir = get_user_dir(username, user_type)
    os.makedirs(user_dir, exist_ok=True)
    
    # Create subdirectories
    os.makedirs(os.path.join(user_dir, "documents"), exist_ok=True)
    os.makedirs(os.path.join(user_dir, "reports"), exist_ok=True)
    os.makedirs(os.path.join(user_dir, "conversations"), exist_ok=True)
    os.makedirs(os.path.join(user_dir, "messages"), exist_ok=True)
    
    if user_type.lower() == "patient":
        os.makedirs(os.path.join(user_dir, "doctor_files"), exist_ok=True)
    elif user_type.lower() == "doctor":
        os.makedirs(os.path.join(user_dir, "patient_files"), exist_ok=True)
    
    return user_dir