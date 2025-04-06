"""
LLM Service
Handles interactions with the Gemini LLM API
"""

import os
import json
import google.generativeai as genai
from config.settings import LLM_SETTINGS

class LLMService:
    """Service for interacting with LLM APIs"""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.model = LLM_SETTINGS["model"]
        self.max_tokens = LLM_SETTINGS["max_tokens"]
        self.temperature = LLM_SETTINGS["temperature"]
        
        # Initialize Gemini API
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def _load_api_key(self):
        """Load API key from file"""
        api_key_file = LLM_SETTINGS["api_key_file"]
        
        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r') as f:
                    data = json.load(f)
                    return data.get("gemini_api_key", "")
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # If we can't load from file, try environment variable
        return os.environ.get("GEMINI_API_KEY", "")
    
    def get_response(self, system_prompt, conversation_history, user_message, callback=None):
        """
        Get a response from the Gemini LLM API with optional streaming
        
        Args:
            system_prompt (str): System instructions for the LLM
            conversation_history (list): Previous conversation messages
            user_message (str): The user's message
            callback (function): Optional callback for streaming responses
            
        Returns:
            str: The LLM's response
        """
        if not self.api_key:
            error_msg = "API key not configured. Please set up your Gemini API key in config/api_keys.json."
            if callback:
                callback(error_msg)
            return error_msg
        
        try:
            # Combine system prompt and conversation history
            full_prompt = system_prompt + "\n\n"
            
            # Add conversation history
            for msg in conversation_history:
                full_prompt += f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}\n"
            
            # Add current user message
            full_prompt += f"User: {user_message}\n"
            full_prompt += "Assistant: "
            
            # Initialize the Gemini model
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            
            # If a callback is provided, use streaming response
            if callback:
                response_text = ""
                
                try:
                    # Stream the response
                    response = model.generate_content(
                        full_prompt,
                        stream=True
                    )
                    
                    for chunk in response:
                        if hasattr(chunk, 'text') and chunk.text:
                            chunk_text = chunk.text
                            response_text += chunk_text
                            callback(chunk_text)
                    
                    return response_text
                
                except Exception as e:
                    error_message = f"Error during streaming: {str(e)}"
                    callback(error_message)
                    return error_message
            
            else:
                # For non-streaming response
                response = model.generate_content(full_prompt)
                return response.text
                
        except Exception as e:
            error_message = f"Error communicating with Gemini API: {str(e)}"
            if callback:
                callback(error_message)
            return error_message
    
    def get_response_sync(self, system_prompt, conversation_history, user_message):
        """
        Get a synchronous response from the Gemini LLM API
        
        Args:
            system_prompt (str): System instructions for the LLM
            conversation_history (list): Previous conversation messages
            user_message (str): The user's message
            
        Returns:
            str: The LLM's response
        """
        return self.get_response(system_prompt, conversation_history, user_message)