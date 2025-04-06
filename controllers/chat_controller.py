"""
Chat Controller
Handles chat interactions with the LLM
"""

import os
import json
import datetime
import threading
from config.settings import get_user_dir
from services.llm_service import LLMService

class ChatController:
    """Controller for chat interactions"""
    
    def __init__(self, user_data):
        self.user_data = user_data
        self.user_dir = get_user_dir(user_data["username"], user_data["user_type"])
        self.conversation_history = []
        self.llm_service = LLMService()
        self.message_queue = None  # This will be set by the view
        
        # Load conversation history if available
        self.load_conversation_history()
    
    def set_message_queue(self, message_queue):
        """Set the message queue for UI updates"""
        self.message_queue = message_queue
    
    def load_conversation_history(self):
        """Load the conversation history from file"""
        conversations_dir = os.path.join(self.user_dir, "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        
        # Get the latest conversation file if it exists
        conversation_files = sorted([
            f for f in os.listdir(conversations_dir) 
            if f.endswith(".json")
        ], reverse=True)
        
        if conversation_files:
            latest_file = os.path.join(conversations_dir, conversation_files[0])
            try:
                with open(latest_file, 'r') as f:
                    self.conversation_history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # Start with empty history if file is corrupt or missing
                self.conversation_history = []
    
    def save_conversation_history(self):
        """Save the conversation history to file"""
        conversations_dir = os.path.join(self.user_dir, "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        
        # Create a new file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        filepath = os.path.join(conversations_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
    
    def add_message(self, sender, message):
        """Add a message to the conversation history"""
        timestamp = datetime.datetime.now().isoformat()
        
        message_entry = {
            "role": "user" if sender == "patient" else "model",
            "content": message
        }
        
        self.conversation_history.append(message_entry)
        
        # Save periodically (could be optimized to save less frequently)
        self.save_conversation_history()
        
        return message_entry
    
    def get_system_prompt(self):
        """Get the system prompt with user context"""
        user_type = self.user_data["user_type"]
        
        if user_type == "patient":
            # Create a context-aware system prompt for patient
            name = self.user_data.get("name", "the patient")
            age = self.user_data.get("age", "")
            gender = self.user_data.get("gender", "")
            medical_history = self.user_data.get("medical_history", "")
            allergies = self.user_data.get("allergies", "")
            
            system_prompt = f"""You are GuideAI, a medical assistant chatbot. 
You are helping {name}, who is a {age}-year-old {gender}.

Medical history: {medical_history}
Allergies: {allergies}

Your role is to provide medical information and guidance while being mindful of these important guidelines:
1. Always include a disclaimer that you are not a substitute for professional medical advice
2. Be clear, compassionate, and informative
3. When uncertain, acknowledge the limitations of your knowledge
4. Encourage seeking proper medical care when appropriate
5. Focus on general education and guidance rather than specific diagnosis
6. Use simple, understandable language

The current date is {datetime.datetime.now().strftime("%Y-%m-%d")}.

Respond to the patient's questions and concerns based on your medical knowledge."""
        else:
            # For doctor users
            system_prompt = """You are GuideAI, a medical assistant chatbot designed to support medical professionals.
You provide information and analysis to help with clinical decision-making while recognizing that the final decisions rest with the qualified healthcare provider.

Your responses should be:
1. Evidence-based and accurate
2. Comprehensive but concise
3. Formatted for easy reading with medical terminology appropriate for professionals
4. Clear about the confidence level of the information

The current date is {datetime.datetime.now().strftime("%Y-%m-%d")}."""
        
        return system_prompt
    
    def process_message(self, message, callback=None):
        """
        Process a user message and get LLM response
        
        Args:
            message (str): User message
            callback (function): Optional callback for streaming response
            
        Returns:
            str: LLM response
        """
        # If no message queue is set, return
        if not self.message_queue:
            print("Message queue not set in ChatController")
            return
        
        # Add thinking message
        self.message_queue.put(("chat", "add_message", ("system", "Thinking...")))
        
        # Run in a background thread to prevent UI blocking
        def process_thread():
            # Get system prompt
            system_prompt = self.get_system_prompt()
            
            # Prepare a callback to update the UI
            def ui_callback(chunk):
                # Put the chunk into the message queue for UI update
                self.message_queue.put(("chat", "add_response_chunk", chunk))
            
            # Get response from LLM
            response = self.llm_service.get_response(
                system_prompt, 
                self.conversation_history[-10:],  # Last 10 messages for context
                message,
                ui_callback  # Use the UI-specific callback
            )
            
            # Add the full response to conversation history
            self.add_message("assistant", response)
        
        # Start processing thread
        threading.Thread(
            target=process_thread,
            daemon=True
        ).start()
    
    def generate_summary(self):
        """Generate a summary of the conversation for the patient record"""
        if not self.conversation_history:
            return "No conversation to summarize."
        
        # Create summary prompt
        summary_prompt = f"""Create a concise medical summary of the following conversation between a patient and a medical assistant.
Focus on key symptoms, concerns, and advice given. Format it as a structured clinical note.

Conversation to summarize:
"""
        
        # Add conversation history to summary
        for entry in self.conversation_history[-20:]:
            role = "Patient" if entry.get("role") == "user" else "Medical Assistant"
            summary_prompt += f"\n{role}: {entry.get('content', '')}"
        
        # Get summary from LLM
        summary = self.llm_service.get_response_sync(
            "You are a medical summarization assistant. Create clear, concise summaries of medical conversations.",
            [],
            summary_prompt
        )
        
        return summary
    
    def save_conversation_summary(self):
        """Generate and save a summary of the conversation"""
        summary = self.generate_summary()
        
        # Save summary to file
        summaries_dir = os.path.join(self.user_dir, "summaries")
        os.makedirs(summaries_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{timestamp}.txt"
        filepath = os.path.join(summaries_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(summary)
        
        return filepath