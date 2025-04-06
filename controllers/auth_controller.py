"""
Authentication Controller
Handles user authentication, login, and registration
"""

import os
import json
import hashlib
from config.settings import CREDENTIALS_FILE, create_user_dir

class AuthController:
    """Controller for handling authentication operations"""
    
    def __init__(self, app):
        self.app = app
        self.load_credentials()
    
    def load_credentials(self):
        """Load user credentials from the JSON file"""
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                self.credentials = json.load(f)
        else:
            self.credentials = {"patients": {}, "doctors": {}}
            self.save_credentials()
    
    def save_credentials(self):
        """Save user credentials to the JSON file"""
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(self.credentials, f, indent=4)
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username, password, user_type):
        """
        Authenticate a user
        
        Args:
            username (str): The username
            password (str): The password
            user_type (str): Either 'patient' or 'doctor'
            
        Returns:
            dict: User data if authentication successful, None otherwise
        """
        user_type = user_type.lower()
        if user_type not in ['patient', 'doctor']:
            return None
        
        user_dict = self.credentials[f"{user_type}s"]
        
        if username in user_dict:
            stored_hash = user_dict[username]["password_hash"]
            if self.hash_password(password) == stored_hash:
                # Return user data without the password hash
                user_data = user_dict[username].copy()
                user_data.pop("password_hash")
                user_data["username"] = username
                user_data["user_type"] = user_type
                return user_data
        
        return None
    
    def register(self, username, password, user_data, user_type):
        """
        Register a new user
        
        Args:
            username (str): The username
            password (str): The password
            user_data (dict): Additional user data (name, age, gender, etc.)
            user_type (str): Either 'patient' or 'doctor'
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        user_type = user_type.lower()
        if user_type not in ['patient', 'doctor']:
            return False
        
        user_dict = self.credentials[f"{user_type}s"]
        
        # Check if username already exists
        if username in user_dict:
            return False
        
        # Store user data with hashed password
        user_dict[username] = user_data.copy()
        user_dict[username]["password_hash"] = self.hash_password(password)
        
        # Create user directory structure
        user_dir = create_user_dir(username, user_type)
        
        # Ensure reports directory exists
        reports_dir = os.path.join(user_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Ensure messages directory exists
        messages_dir = os.path.join(user_dir, "messages")
        os.makedirs(messages_dir, exist_ok=True)
        
        # Save updated credentials
        self.save_credentials()
        
        # Return complete user data for session
        result_data = user_data.copy()
        result_data["username"] = username
        result_data["user_type"] = user_type
        
        return result_data
    
    def authenticate_and_redirect(self, username, password, user_type):
        """Authenticate user and redirect to appropriate view"""
        user_data = self.login(username, password, user_type)
        
        if user_data:
            if user_type.lower() == "patient":
                self.app.show_patient_view(user_data)
            else:
                self.app.show_doctor_view(user_data)
            return True
        
        return False