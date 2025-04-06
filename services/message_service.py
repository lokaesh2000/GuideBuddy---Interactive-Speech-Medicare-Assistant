"""
Message Service
Handles storage and retrieval of messages between users
"""

import os
import json
import time
from datetime import datetime

from config.settings import get_user_dir

class MessageService:
    """Service for handling messages between users"""
    
    def __init__(self, sender_data):
        """
        Initialize the message service
        
        Args:
            sender_data (dict): Data about the sender (username, user_type)
        """
        self.sender_data = sender_data
        self.sender_username = sender_data["username"]
        self.sender_type = sender_data["user_type"]
        self.sender_dir = get_user_dir(self.sender_username, self.sender_type)
        self.messages_dir = os.path.join(self.sender_dir, "messages")
        
        # Ensure messages directory exists
        os.makedirs(self.messages_dir, exist_ok=True)
    
    def send_message(self, recipient_username, recipient_type, message_text):
        """
        Send a message to another user
        
        Args:
            recipient_username (str): Username of the recipient
            recipient_type (str): Type of the recipient (patient or doctor)
            message_text (str): Content of the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create message data
            timestamp = datetime.now().isoformat()
            
            message_data = {
                "sender_username": self.sender_username,
                "sender_type": self.sender_type,
                "recipient_username": recipient_username,
                "recipient_type": recipient_type,
                "timestamp": timestamp,
                "content": message_text
            }
            
            # Save message in sender's directory
            self._save_message_to_conversation(
                self.messages_dir, 
                recipient_username, 
                message_data
            )
            
            # Save message in recipient's directory
            recipient_dir = get_user_dir(recipient_username, recipient_type)
            recipient_messages_dir = os.path.join(recipient_dir, "messages")
            os.makedirs(recipient_messages_dir, exist_ok=True)
            
            self._save_message_to_conversation(
                recipient_messages_dir,
                self.sender_username,
                message_data
            )
            
            # Sleep briefly to ensure file operations complete
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
    
    def get_conversation(self, other_username):
        """
        Get the conversation history with another user
        
        Args:
            other_username (str): Username of the other user
            
        Returns:
            list: List of message dictionaries
        """
        conversation_file = self._get_conversation_file_path(other_username)
        
        if not os.path.exists(conversation_file):
            return []
        
        try:
            with open(conversation_file, 'r') as f:
                data = json.load(f)
                # Sort messages by timestamp to ensure proper order
                return sorted(data, key=lambda x: x.get('timestamp', ''))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading conversation: {str(e)}")
            return []
    
    def _save_message_to_conversation(self, base_dir, other_username, message_data):
        """
        Save a message to a conversation file
        
        Args:
            base_dir (str): Base directory for messages
            other_username (str): Username of the other participant
            message_data (dict): Message data to save
        """
        # Ensure directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Get conversation file path
        conversation_file = os.path.join(base_dir, f"{other_username}.json")
        
        # Load existing conversation or create new
        conversation = []
        if os.path.exists(conversation_file):
            try:
                with open(conversation_file, 'r') as f:
                    conversation = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                conversation = []
        
        # Add new message
        conversation.append(message_data)
        
        # Save updated conversation
        with open(conversation_file, 'w') as f:
            json.dump(conversation, f, indent=2)
    
    def _get_conversation_file_path(self, other_username):
        """
        Get the path to a conversation file
        
        Args:
            other_username (str): Username of the other participant
            
        Returns:
            str: Path to the conversation file
        """
        return os.path.join(self.messages_dir, f"{other_username}.json")
    
    def get_all_conversations(self):
        """
        Get a list of all conversations
        
        Returns:
            list: List of usernames with whom the user has conversations
        """
        if not os.path.exists(self.messages_dir):
            return []
        
        conversations = []
        for filename in os.listdir(self.messages_dir):
            if filename.endswith('.json'):
                username = filename[:-5]  # Remove .json extension
                conversations.append(username)
        
        return conversations