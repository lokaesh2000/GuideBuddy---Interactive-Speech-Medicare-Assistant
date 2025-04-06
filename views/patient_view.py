"""
Patient View
Main interface for patient users - Updated layout
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import queue
import json

from config.settings import get_user_dir, CREDENTIALS_FILE
from controllers.chat_controller import ChatController
from controllers.document_controller import DocumentController
from services.speech_service import SpeechService
from services.message_service import MessageService
from agents.specialist_agent import SpecialistAgent

class ChatPanel(ttk.LabelFrame):
    """Chat panel UI component"""
    
    def __init__(self, parent, chat_controller, speech_service, message_queue):
        super().__init__(parent, text="AI Medical Assistant")
        
        self.chat_controller = chat_controller
        self.speech_service = speech_service
        self.message_queue = message_queue
        self.is_recording = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the chat UI"""
        # Chat display
        self.chat_display = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.tag_configure("user", foreground="#0066cc")
        self.chat_display.tag_configure("assistant", foreground="#FF0000")
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
        
        # Get response from LLM
        self.add_system_message("Thinking...")
        self.chat_controller.process_message(
            message,
            callback=self.handle_response_chunk
        )
    
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
                
                # Get AI response
                self.message_queue.put(("chat", "add_message", ("system", "Thinking...")))
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
    def add_response_chunk(self, text_chunk):
        """Add a chunk of response text to the display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Clear any "Thinking..." messages first
        self.clear_system_messages()
        
        # Check if we already have a message from the assistant
        content = self.chat_display.get("1.0", tk.END)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if "AI Assistant:" not in content:
            # First chunk - add with timestamp
            self.chat_display.insert(tk.END, f"[{timestamp}] AI Assistant: {text_chunk}", "assistant")
        else:
            # Append to existing message
            # Find the last occurrence of "AI Assistant:"
            last_pos = content.rfind("AI Assistant:")
            if last_pos != -1:
                # Insert at the end of the message
                self.chat_display.insert(tk.END, text_chunk, "assistant")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def handle_response_chunk(self, text_chunk):
        """Handle a chunk of streaming response"""
        if text_chunk:
            # Update the message display immediately
            self.message_queue.put(("chat", "add_response_chunk", text_chunk))
            
            # Use text-to-speech if enabled
            if self.tts_var.get():
                self.speech_service.speak_text(text_chunk)
    
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
            # Clear any "Thinking..." message
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


class DocumentPanel(ttk.LabelFrame):
    """Document panel UI component"""
    
    def __init__(self, parent, document_controller, message_queue):
        super().__init__(parent, text="Medical Documents")
        
        self.document_controller = document_controller
        self.message_queue = message_queue
        self.processing = False
        
        self.setup_ui()
        self.update_document_list()
    
    def setup_ui(self):
        """Set up the document panel UI"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Document list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(list_frame, text="Uploaded Documents:").pack(anchor=tk.W)
        
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.document_listbox = tk.Listbox(list_container)
        self.document_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.document_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.document_listbox.config(yscrollcommand=scrollbar.set)
        
        # Document actions
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        upload_button = ttk.Button(
            action_frame, 
            text="Upload Document",
            command=self.upload_document
        )
        upload_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete",
            command=self.delete_document
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Analysis section
        analysis_frame = ttk.Frame(main_frame)
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.analyze_button = ttk.Button(
            analysis_frame, 
            text="Analyze Documents",
            command=self.analyze_documents
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        # Progress indicator
        self.progress_var = tk.StringVar(value="Ready")
        progress_label = ttk.Label(analysis_frame, textvariable=self.progress_var)
        progress_label.pack(side=tk.LEFT, padx=5)
        
        # Reports section
        reports_frame = ttk.LabelFrame(main_frame, text="Analysis Reports")
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        reports_container = ttk.Frame(reports_frame)
        reports_container.pack(fill=tk.BOTH, expand=True)
        
        self.reports_listbox = tk.Listbox(reports_container)
        self.reports_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        reports_scrollbar = ttk.Scrollbar(reports_container, orient=tk.VERTICAL, command=self.reports_listbox.yview)
        reports_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reports_listbox.config(yscrollcommand=reports_scrollbar.set)
        
        # Reports actions
        report_action_frame = ttk.Frame(reports_frame)
        report_action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        view_report_button = ttk.Button(
            report_action_frame, 
            text="View Report",
            command=self.view_report
        )
        view_report_button.pack(side=tk.LEFT, padx=5)
        
        # Update reports list
        self.update_reports_list()
    
    def upload_document(self):
        """Handle document upload"""
        file_paths = filedialog.askopenfilenames(
            title="Select Medical Documents",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_paths:
            return  # User cancelled
        
        for file_path in file_paths:
            # Start upload in background thread
            threading.Thread(
                target=self._upload_document_thread,
                args=(file_path,),
                daemon=True
            ).start()
    
    def _upload_document_thread(self, file_path):
        """Upload document in background thread"""
        self.progress_var.set(f"Uploading {os.path.basename(file_path)}...")
        
        result = self.document_controller.upload_document(
            file_path,
            callback=self.handle_callback
        )
        
        if result:
            # Update document list in UI thread
            self.message_queue.put(("documents", "update_list", None))
            self.progress_var.set("Upload complete")
        else:
            self.progress_var.set("Upload failed")
    
    def delete_document(self):
        """Delete selected document"""
        selected = self.document_listbox.curselection()
        if not selected:
            messagebox.showinfo("Document Selection", "Please select a document to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this document?"):
            document_path = self.document_paths[selected[0]]
            result = self.document_controller.delete_document(document_path)
            
            if result:
                self.update_document_list()
                self.progress_var.set("Document deleted")
            else:
                self.progress_var.set("Delete failed")
    
    def analyze_documents(self):
        """Analyze selected documents"""
        selected = self.document_listbox.curselection()
        if not selected:
            messagebox.showinfo("Document Selection", "Please select documents to analyze")
            return
        
        # Get selected document paths
        selected_paths = [self.document_paths[i] for i in selected]
        
        if self.processing:
            messagebox.showinfo("Processing", "Document analysis is already in progress")
            return
        
        # Update UI state
        self.processing = True
        self.analyze_button.config(state=tk.DISABLED)
        self.progress_var.set("Starting analysis...")
        
        # Start analysis in background thread
        self.document_controller.process_documents(
            selected_paths,
            callback=self.handle_callback
        )
    
    def update_document_list(self):
        """Update the list of documents"""
        self.document_listbox.delete(0, tk.END)
        self.document_paths = self.document_controller.get_documents()
        
        for path in self.document_paths:
            filename = os.path.basename(path)
            self.document_listbox.insert(tk.END, filename)
    
    def update_reports_list(self):
        """Update the list of reports"""
        self.reports_listbox.delete(0, tk.END)
        self.report_paths = self.document_controller.get_reports()
        
        for path in self.report_paths:
            filename = os.path.basename(path)
            self.reports_listbox.insert(tk.END, filename)
    
    def view_report(self):
        """View selected report"""
        selected = self.reports_listbox.curselection()
        if not selected:
            messagebox.showinfo("Report Selection", "Please select a report to view")
            return
        
        report_path = self.report_paths[selected[0]]
        
        # Check if the file exists and try to open it
        if os.path.exists(report_path):
            import platform
            import subprocess
            
            system = platform.system()
            
            try:
                if system == 'Windows':
                    os.startfile(report_path)
                elif system == 'Darwin':  # macOS
                    subprocess.call(['open', report_path])
                else:  # Linux
                    subprocess.call(['xdg-open', report_path])
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open file: {str(e)}")
        else:
            messagebox.showerror("File Error", "Report file not found")
    
    def handle_callback(self, event_type, data):
        """Handle callbacks from document controller"""
        if event_type == "status":
            self.progress_var.set(data)
        
        elif event_type == "document_added":
            self.message_queue.put(("documents", "update_list", None))
        
        elif event_type == "report_generated":
            # Reset processing state
            self.processing = False
            self.analyze_button.config(state=tk.NORMAL)
            
            # Update reports list
            self.update_reports_list()
            
            # Show success message
            messagebox.showinfo("Analysis Complete", "Document analysis has been completed and a report has been generated.")


class SpecialistChatPanel(ttk.LabelFrame):
    """Specialist chat panel UI component"""
    
    def __init__(self, parent, user_data, message_queue):
        super().__init__(parent, text="Specialist Consultation")
        
        self.user_data = user_data
        self.message_queue = message_queue
        self.specialist_agent = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the specialist chat UI"""
        # Specialist selector
        specialist_select_frame = ttk.Frame(self)
        specialist_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(specialist_select_frame, text="Select Specialist:").pack(side=tk.LEFT, padx=5)
        
        self.specialist_var = tk.StringVar()
        specialists = ["Cardiologist", "Neurologist", "Orthopedist", "Pediatrician", 
                      "Dermatologist", "Ophthalmologist", "Gynecologist", "Psychiatrist"]
        
        self.specialist_combo = ttk.Combobox(
            specialist_select_frame, 
            textvariable=self.specialist_var,
            values=specialists,
            width=20
        )
        self.specialist_combo.pack(side=tk.LEFT, padx=5)
        
        connect_button = ttk.Button(
            specialist_select_frame, 
            text="Connect", 
            command=self.connect_to_specialist
        )
        connect_button.pack(side=tk.LEFT, padx=5)
        
        # Chat area
        self.chat_text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.tag_configure("user", foreground="#0066cc")
        self.chat_text.tag_configure("specialist", foreground="#cc0000")
        self.chat_text.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.bind("<Return>", lambda e: self.send_to_specialist())
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        send_button = ttk.Button(
            input_frame, 
            text="Send",
            command=self.send_to_specialist
        )
        send_button.pack(side=tk.LEFT, padx=5)
        
        speech_button = ttk.Button(
            input_frame, 
            text="🎤",
            command=self.specialist_speech_input
        )
        speech_button.pack(side=tk.LEFT, padx=5)
    
    def connect_to_specialist(self):
        """Connect to a medical specialist"""
        specialist = self.specialist_var.get()
        if not specialist:
            messagebox.showwarning("Specialist Selection", "Please select a specialist type")
            return
        
        # Clear the chat
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # Add welcome message
        self.add_message("system", f"Connecting to {specialist}... Please wait.")
        
        # Initialize specialist agent
        self.specialist_agent = SpecialistAgent(specialist, self.user_data)
        
        # Get initial greeting from specialist
        threading.Thread(
            target=self.get_specialist_greeting,
            daemon=True
        ).start()
    
    def get_specialist_greeting(self):
        """Get initial greeting from the specialist"""
        if not self.specialist_agent:
            return
        
        # Use a generic greeting prompt
        greeting = self.specialist_agent.get_response(
            "Hello, I would like to consult with you about my health concerns."
        )
        
        # Add to chat
        self.message_queue.put(("specialist", "add_message", ("specialist", greeting)))
    
    def send_to_specialist(self):
        """Send a message to the specialist"""
        if not self.specialist_agent:
            messagebox.showinfo("Specialist", "Please connect to a specialist first")
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Add user message to chat
        self.add_message("user", message)
        
        # Clear input
        self.message_entry.delete(0, tk.END)
        
        # Process in background thread
        threading.Thread(
            target=self.process_specialist_message,
            args=(message,),
            daemon=True
        ).start()
    
    def process_specialist_message(self, message):
        """Process a message sent to the specialist agent"""
        if not self.specialist_agent:
            return
        
        # Add "thinking" indicator
        self.message_queue.put(("specialist", "add_message", ("system", "The specialist is typing...")))
        
        # Get response from specialist agent
        response = self.specialist_agent.get_response(message)
        
        # Remove "thinking" indicator
        self.message_queue.put(("specialist", "remove_thinking", None))
        
        # Add to message queue for UI update
        self.message_queue.put(("specialist", "add_message", ("specialist", response)))
    
    def specialist_speech_input(self):
        """Handle speech input for specialist chat"""
        if not self.specialist_agent:
            messagebox.showinfo("Specialist", "Please connect to a specialist first")
            return
        
        # This will be implemented with the speech service
        from services.speech_service import SpeechService
        speech_service = SpeechService()
        
        # Add a message to indicate recording
        self.add_message("system", "Listening...")
        
        # Start recording in a background thread
        threading.Thread(
            target=self.capture_speech_for_specialist,
            args=(speech_service,),
            daemon=True
        ).start()
    
    def capture_speech_for_specialist(self, speech_service):
        """Capture speech input in a background thread"""
        try:
            # Record and transcribe
            transcript = speech_service.record_and_transcribe()
            
            if transcript:
                # Add transcribed text as user message
                self.message_queue.put(("specialist", "add_message", ("user", transcript)))
                
                # Process the message
                self.process_specialist_message(transcript)
            else:
                self.message_queue.put(("specialist", "add_message", ("system", "No speech detected. Please try again.")))
        except Exception as e:
            self.message_queue.put(("specialist", "add_message", ("system", f"Error processing speech: {str(e)}")))
    
    def add_message(self, sender, message):
        """Add a message to the specialist chat"""
        self.chat_text.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "system":
            # Check if there's a "typing" message to remove
            if "typing" in message.lower():
                # Store this as the last "typing" position
                self.last_typing_position = self.chat_text.index(tk.END)
            self.chat_text.insert(tk.END, f"[{timestamp}] {message}\n\n", "system")
        elif sender == "user":
            self.chat_text.insert(tk.END, f"[{timestamp}] You: {message}\n\n", "user")
        else:
            # Remove any "typing" messages
            content = self.chat_text.get("1.0", tk.END)
            if "typing" in content.lower():
                lines = content.split("\n")
                filtered_lines = [line for line in lines if "typing" not in line.lower()]
                new_content = "\n".join(filtered_lines)
                
                self.chat_text.delete("1.0", tk.END)
                self.chat_text.insert(tk.END, new_content)
            
            # Add specialist message
            self.chat_text.insert(tk.END, f"[{timestamp}] Specialist: {message}\n\n", "specialist")
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def remove_thinking_indicator(self):
        """Remove the 'specialist is typing' message"""
        self.chat_text.config(state=tk.NORMAL)
        
        # Find and remove typing messages
        content = self.chat_text.get("1.0", tk.END)
        lines = content.split("\n")
        filtered_lines = []
        
        for line in lines:
            if "typing" not in line.lower():
                filtered_lines.append(line)
        
        new_content = "\n".join(filtered_lines)
        
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.insert(tk.END, new_content)
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)


class FileManagementPanel(ttk.LabelFrame):
    """File management panel UI component"""
    
    def __init__(self, parent, user_data):
        super().__init__(parent, text="Files & Communication")
        
        self.user_data = user_data
        self.user_dir = get_user_dir(user_data["username"], "patient")
        self.message_service = MessageService(user_data)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the file management UI"""
        # Create notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files from doctors tab
        self.files_tab = ttk.Frame(self.notebook)
        self.setup_files_tab()
        self.notebook.add(self.files_tab, text="Files")
        
        # Messages tab
        self.messages_tab = ttk.Frame(self.notebook)
        self.setup_messages_tab()
        self.notebook.add(self.messages_tab, text="Messages")
    
    def setup_files_tab(self):
        """Set up the files tab"""
        # Container frame
        container = ttk.Frame(self.files_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side: Doctor folders
        folders_frame = ttk.LabelFrame(container, text="Doctor Files")
        folders_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Refresh button
        refresh_button = ttk.Button(
            folders_frame,
            text="🔄 Refresh",
            command=self.refresh_folders
        )
        refresh_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Doctor folders list
        self.folders_listbox = tk.Listbox(folders_frame)
        self.folders_listbox.bind("<<ListboxSelect>>", self.update_files_list)
        self.folders_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side: Files list
        files_frame = ttk.LabelFrame(container, text="Files")
        files_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files list
        self.files_listbox = tk.Listbox(files_frame)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File actions
        file_actions = ttk.Frame(files_frame)
        file_actions.pack(fill=tk.X, padx=5, pady=5)
        
        view_button = ttk.Button(
            file_actions,
            text="View File",
            command=self.view_file
        )
        view_button.pack(side=tk.LEFT, padx=5)
        
        # Load initial data
        self.refresh_folders()
    
    def setup_messages_tab(self):
        """Set up the messages tab"""
        # Container frame
        container = ttk.Frame(self.messages_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Doctor selector
        select_frame = ttk.Frame(container)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Send message to:").pack(side=tk.LEFT, padx=5)
        
        self.doctor_var = tk.StringVar()
        self.doctor_combo = ttk.Combobox(
            select_frame,
            textvariable=self.doctor_var,
            width=20
        )
        self.doctor_combo.pack(side=tk.LEFT, padx=5)
        self.doctor_combo.bind("<<ComboboxSelected>>", self.load_conversation)
        
        refresh_button = ttk.Button(
            select_frame,
            text="🔄",
            command=self.load_doctors,
            width=3
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Message display
        self.messages_text = tk.Text(container, wrap=tk.WORD, state=tk.DISABLED)
        self.messages_text.tag_configure("sent", foreground="#0066cc")
        self.messages_text.tag_configure("received", foreground="#006633")
        self.messages_text.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
        self.messages_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(container)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        send_button.pack(side=tk.LEFT, padx=5)
        
        # Load doctors
        self.load_doctors()
    
    def refresh_folders(self):
        """Refresh the list of doctor folders"""
        self.folders_listbox.delete(0, tk.END)
        
        doctor_files_dir = os.path.join(self.user_dir, "doctor_files")
        if not os.path.exists(doctor_files_dir):
            return
        
        for folder in os.listdir(doctor_files_dir):
            folder_path = os.path.join(doctor_files_dir, folder)
            if os.path.isdir(folder_path):
                self.folders_listbox.insert(tk.END, folder)
    
    def update_files_list(self, event=None):
        """Update files list based on selected doctor folder"""
        self.files_listbox.delete(0, tk.END)
        
        selected = self.folders_listbox.curselection()
        if not selected:
            return
        
        folder = self.folders_listbox.get(selected[0])
        folder_path = os.path.join(self.user_dir, "doctor_files", folder)
        
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    self.files_listbox.insert(tk.END, file)
    
    def view_file(self):
        """View the selected file"""
        selected_folder = self.folders_listbox.curselection()
        selected_file = self.files_listbox.curselection()
        
        if not selected_folder or not selected_file:
            messagebox.showinfo("Selection", "Please select a doctor folder and a file")
            return
        
        folder = self.folders_listbox.get(selected_folder[0])
        filename = self.files_listbox.get(selected_file[0])
        
        file_path = os.path.join(self.user_dir, "doctor_files", folder, filename)
        
        if os.path.exists(file_path):
            import subprocess
            import platform
            
            system = platform.system()
            
            try:
                if system == 'Windows':
                    os.startfile(file_path)
                elif system == 'Darwin':  # macOS
                    subprocess.call(['open', file_path])
                else:  # Linux
                    subprocess.call(['xdg-open', file_path])
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open file: {str(e)}")
        else:
            messagebox.showerror("File Error", "File not found")
    
    def load_doctors(self):
        """Load list of doctors from credentials"""
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
                doctors = credentials.get("doctors", {})
                
                doctor_names = []
                self.doctor_usernames = {}
                
                for username, data in doctors.items():
                    name = data.get("name", username)
                    display_name = f"{name} ({username})"
                    doctor_names.append(display_name)
                    self.doctor_usernames[display_name] = username
                
                self.doctor_combo['values'] = doctor_names
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    def load_conversation(self, event=None):
        """Load conversation with selected doctor"""
        selected_doctor = self.doctor_var.get()
        if not selected_doctor or not hasattr(self, 'doctor_usernames'):
            print("No doctor selected or doctor_usernames dictionary not available")
            return
        
        if selected_doctor not in self.doctor_usernames:
            print(f"Selected doctor {selected_doctor} not found in doctor_usernames dictionary")
            return
        
        doctor_username = self.doctor_usernames[selected_doctor]
        print(f"Loading conversation with doctor {doctor_username}")
        
        # Get conversation history
        conversation = self.message_service.get_conversation(doctor_username)
        print(f"Found {len(conversation)} messages in conversation")
        
        # Display conversation
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        
        if not conversation:
            self.messages_text.insert(tk.END, "No previous messages with this doctor.\n")
        else:
            for message in conversation:
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                sender = message["sender_username"]
                content = message["content"]
                
                if sender == self.user_data["username"]:
                    # Message sent by the patient
                    self.messages_text.insert(tk.END, f"[{timestamp}] You: {content}\n\n", "sent")
                else:
                    # Message received from the doctor
                    doctor_name = selected_doctor.split(" (")[0]
                    self.messages_text.insert(tk.END, f"[{timestamp}] Dr. {doctor_name}: {content}\n\n", "received")
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def send_message(self):
        """Send a message to a doctor"""
        doctor = self.doctor_var.get()
        message = self.message_entry.get().strip()
        
        if not doctor:
            messagebox.showwarning("Doctor Selection", "Please select a doctor")
            return
        
        if not message:
            return
        
        if not hasattr(self, 'doctor_usernames') or doctor not in self.doctor_usernames:
            messagebox.showwarning("Doctor Selection", "Invalid doctor selection")
            return
        
        # Get doctor username
        doctor_username = self.doctor_usernames[doctor]
        
        # Send the message
        success = self.message_service.send_message(
            doctor_username,
            "doctor",
            message
        )
        
        if success:
            # Add message to display
            self.messages_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.messages_text.insert(tk.END, f"[{timestamp}] You: {message}\n\n", "sent")
            self.messages_text.see(tk.END)
            self.messages_text.config(state=tk.DISABLED)
            
            # Clear input
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Message Error", "Failed to send message")


class PatientView(ttk.Frame):
    """Main view for patient interactions - Updated layout"""
    
    def __init__(self, parent, user_data, app):
        super().__init__(parent)
        self.user_data = user_data
        self.app = app
        self.user_dir = get_user_dir(user_data["username"], "patient")
        
        # Create message queue FIRST
        self.message_queue = queue.Queue()
        
        # Initialize controllers
        self.chat_controller = ChatController(self.user_data)
        self.document_controller = DocumentController(self.user_data)
        
        # Initialize speech service
        self.speech_service = SpeechService()
        
        # Set message queue in chat controller AFTER creating it
        self.chat_controller.set_message_queue(self.message_queue)
        
        # UI Components
        self.setup_ui()
        
        # Start processing the message queue
        self.process_message_queue()
    
    def setup_ui(self):
        """Set up the patient interface with the new layout"""
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Profile header at the top
        self.setup_profile_header(main_container)
        
        # Main content area (takes the rest of the space)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns for left and right sides
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        
        # Left side: Stacked chat panels (Medical assistant and specialist)
        left_panel = ttk.Frame(content_frame)
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Configure the left panel to have two rows
        left_panel.rowconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)
        
        # Medical Assistant Chat
        self.chat_panel = ChatPanel(
            left_panel, 
            self.chat_controller, 
            self.speech_service,
            self.message_queue
        )
        self.chat_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=5)
        
        # Specialist Chat
        self.specialist_panel = SpecialistChatPanel(
            left_panel,
            self.user_data,
            self.message_queue
        )
        self.specialist_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)
        
        # Right side: Document panel on top, file management on bottom
        # Document panel (upper right)
        self.document_panel = DocumentPanel(
            content_frame, 
            self.document_controller,
            self.message_queue
        )
        self.document_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # File Management Panel (lower right)
        self.file_panel = FileManagementPanel(
            content_frame,
            self.user_data
        )
        self.file_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Add logout button
        logout_button = ttk.Button(main_container, text="Logout", command=self.logout)
        logout_button.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def setup_profile_header(self, parent):
        """Create a compact profile header"""
        header_frame = ttk.Frame(parent, relief=tk.GROOVE, borderwidth=1)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(
            header_frame, 
            text="Patient Profile", 
            font=("Arial", 12, "bold"),
            padding=(5, 5, 5, 5)
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Basic info layout
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Create a grid of labels for patient information
        labels = [
            ("Name:", self.user_data.get("name", "")),
            ("Age:", self.user_data.get("age", "")),
            ("Gender:", self.user_data.get("gender", "")),
            ("Email:", self.user_data.get("email", ""))
        ]
        
        for i, (label, value) in enumerate(labels):
            ttk.Label(info_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(info_frame, text=value).grid(
                row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2
            )
    
    def process_message_queue(self):
        """Process messages from the queue to update UI"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                target, action, data = message
                
                if target == "chat":
                    if action == "add_message":
                        self.chat_panel.add_message(data[0], data[1])
                    elif action == "add_response_chunk":
                        # This would handle streaming responses
                        self.chat_panel.add_response_chunk(data)
                        pass
                
                elif target == "specialist":
                    if action == "add_message":
                        self.specialist_panel.add_message(data[0], data[1])
                    elif action == "remove_thinking":
                        self.specialist_panel.remove_thinking_indicator()
                
                elif target == "documents":
                    if action == "update_list":
                        self.document_panel.update_document_list()
                
                elif target == "ui":
                    if action == "reset_speak_button":
                        self.chat_panel.speak_button.configure(text="🎤")
                
                self.message_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Schedule to run again after 100ms
            self.after(100, self.process_message_queue)
    
    def logout(self):
        """Log out the current user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.show_auth_view()