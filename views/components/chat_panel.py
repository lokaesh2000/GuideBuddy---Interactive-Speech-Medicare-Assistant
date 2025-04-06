"""
Chat Panel Component
Reusable UI component for chat interface
"""

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
import queue

class ChatPanel(ttk.LabelFrame):
    """Chat panel UI component"""
    
    def __init__(self, parent, chat_controller, speech_service, message_queue):
        super().__init__(parent, text="AI Medical Assistant")
        
        self.chat_controller = chat_controller
        self.speech_service = speech_service
        self.message_queue = message_queue
        self.is_recording = False
        
        # Queue to handle response chunks
        self.response_queue = queue.Queue()
        
        self.setup_ui()
        self.start_response_processor()
    
    def setup_ui(self):
        """Set up the chat UI"""
        # Chat display
        self.chat_display = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.tag_configure("user", foreground="#0066cc")
        self.chat_display.tag_configure("assistant", foreground="#006633")
        self.chat_display.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
        
        chat_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scrollbar.set)
        
        # Input area
        self.input_frame = ttk.Frame(self)
        
        self.message_entry = ttk.Entry(self.input_frame)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = ttk.Button(
            self.input_frame, 
            text="Send", 
            command=self.send_message
        )
        
        self.speak_button = ttk.Button(
            self.input_frame, 
            text="🎤", 
            command=self.toggle_speech_input
        )
        
        self.tts_var = tk.BooleanVar(value=True)
        self.tts_checkbox = ttk.Checkbutton(
            self.input_frame,
            text="Text-to-Speech",
            variable=self.tts_var
        )
        
        # Layout
        self.chat_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.send_button.pack(side=tk.LEFT, padx=5)
        self.speak_button.pack(side=tk.LEFT, padx=5)
        self.tts_checkbox.pack(side=tk.RIGHT, padx=5)
        
        # Add welcome message
        self.add_system_message("Welcome to GuideAI. How can I assist you with your medical questions?")
    
    def start_response_processor(self):
        """Start a thread to process response chunks"""
        def process_response_chunks():
            current_response = ""
            while True:
                try:
                    chunk = self.response_queue.get(timeout=0.1)
                    if chunk is None:  # Sentinel to stop processing
                        break
                    
                    current_response += chunk
                    
                    # Update UI with the current response
                    self.update_assistant_response(current_response)
                    
                    # Speak the chunk if TTS is enabled
                    if self.tts_var.get():
                        self.speech_service.speak_text(chunk)
                
                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"Error processing response: {e}")
        
        self.response_thread = threading.Thread(
            target=process_response_chunks,
            daemon=True
        )
        self.response_thread.start()
    
    def update_assistant_response(self, response):
        """Update the assistant's response in the chat display"""
        # This method should be called from the main thread
        def update():
            self.chat_display.config(state=tk.NORMAL)
            
            # Clear previous response
            try:
                # Find the last occurrence of "AI Assistant:"
                last_assistant_index = self.chat_display.search("AI Assistant:", "1.0", tk.END, backwards=True)
                if last_assistant_index:
                    # Delete everything from that point to the end
                    self.chat_display.delete(last_assistant_index, tk.END)
                else:
                    # If no previous assistant message, add timestamp
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.chat_display.insert(tk.END, f"\n[{timestamp}] AI Assistant: ", "assistant")
                
                # Insert the updated response
                self.chat_display.insert(tk.END, response, "assistant")
            except Exception as e:
                print(f"Error updating response: {e}")
            
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        
        # Schedule the update in the main thread
        self.after(0, update)
    
    def send_message(self):
        """Send a text message"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Clear input field
        self.message_entry.delete(0, tk.END)
        
        # Add message to chat
        self.add_message("patient", message)
        
        # Save message to conversation history
        self.chat_controller.add_message("patient", message)
        
        # Clear any existing response
        self.clear_response_processing()
        
        # Add thinking message
        self.add_system_message("Thinking...")
        
        # Process message with streaming callback
        self.chat_controller.process_message(
            message,
            callback=self.handle_response_chunk
        )
    
    def clear_response_processing(self):
        """Clear any ongoing response processing"""
        # Add a sentinel value to stop the response thread if it's running
        try:
            self.response_queue.put(None)
        except Exception:
            pass
        
        # Clear the queue
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except queue.Empty:
                break
    
    def toggle_speech_input(self):
        """Toggle speech input on/off"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording audio for speech input"""
        self.is_recording = True
        self.speak_button.configure(text="⏹️")
        self.add_system_message("Listening...")
        
        # Start recording in a background thread
        threading.Thread(
            target=self.record_audio,
            daemon=True
        ).start()
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        self.speak_button.configure(text="🎤")
        self.speech_service.stop_recording()
    
    def record_audio(self):
        """Record audio and process speech input"""
        try:
            # Use speech service to record and transcribe
            transcript = self.speech_service.record_and_transcribe()
            
            if transcript:
                # Add transcript to chat
                self.message_queue.put(("chat", "add_message", ("patient", transcript)))
                
                # Save to conversation history
                self.chat_controller.add_message("patient", transcript)
                
                # Clear any existing response
                self.clear_response_processing()
                
                # Add thinking message
                self.message_queue.put(("chat", "add_message", ("system", "Thinking...")))
                
                # Get AI response
                self.chat_controller.process_message(
                    transcript,
                    callback=self.handle_response_chunk
                )
            else:
                self.message_queue.put(("chat", "add_message", ("system", "No speech detected. Please try again.")))
        
        except Exception as e:
            self.message_queue.put(("chat", "add_message", ("system", f"Error processing speech: {str(e)}")))
        
        finally:
            # Reset recording state
            self.is_recording = False
            self.message_queue.put(("ui", "reset_speak_button", None))
    
    def handle_response_chunk(self, text_chunk):
        """Handle a chunk of streaming response"""
        if text_chunk:
            # Put the chunk into the response queue
            self.response_queue.put(text_chunk)
    
    def add_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "system":
            self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n\n", "system")
        elif sender == "patient":
            self.chat_display.insert(tk.END, f"[{timestamp}] You: {message}\n\n", "user")
        else:
            # Clear any "Thinking..." messages
            self.clear_system_messages()
            
            # Add assistant message
            self.chat_display.insert(tk.END, f"[{timestamp}] AI Assistant: {message}\n\n", "assistant")
            
            # Save message to conversation history
            self.chat_controller.add_message("assistant", message)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_system_message(self, message):
        """Add a system message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n\n", "system")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def clear_system_messages(self):
        """Clear system messages like 'Thinking...'"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Find and remove "Thinking..." messages
        content = self.chat_display.get("1.0", tk.END)
        lines = content.split("\n")
        filtered_lines = []
        
        for line in lines:
            if "Thinking..." not in line:
                filtered_lines.append(line)
        
        new_content = "\n".join(filtered_lines)
        
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.insert("1.0", new_content)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)