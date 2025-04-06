"""
Doctor View
Main interface for doctor users - Updated layout
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
        
        # Layout
        self.chat_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.send_button.pack(side=tk.LEFT, padx=5)
        self.speak_button.pack(side=tk.LEFT, padx=5)
        
        # Add welcome message
        self.add_system_message("Welcome to GuideAI Doctor Assistant. How can I help you today?")
    
    def send_message(self):
        """Send a text message"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Clear input field
        self.message_entry.delete(0, tk.END)
        
        # Add message to chat
        self.add_message("doctor", message)
        
        # Save message to conversation history
        self.chat_controller.add_message("doctor", message)
        
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
                self.message_queue.put(("chat", "add_message", ("doctor", transcript)))
                
                # Save to conversation history
                self.chat_controller.add_message("doctor", transcript)
                
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
    
    def handle_response_chunk(self, text_chunk):
        """Handle a chunk of streaming response"""
        if text_chunk:
            # This is called from a background thread, so we need to use the message queue
            self.message_queue.put(("chat", "add_response_chunk", text_chunk))
    
    def add_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "system":
            self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n\n", "system")
        elif sender == "doctor":
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


class PatientManagementPanel(ttk.LabelFrame):
    """Patient management panel UI component"""
    
    def __init__(self, parent, user_data):
        super().__init__(parent, text="Patient Management")
        
        self.user_data = user_data
        self.user_dir = get_user_dir(user_data["username"], "doctor")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the patient management UI"""
        # Container with patients and files
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Left side: Patient list
        patients_frame = ttk.LabelFrame(main_container, text="My Patients")
        patients_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Refresh button
        refresh_button = ttk.Button(
            patients_frame,
            text="🔄 Refresh",
            command=self.refresh_patients
        )
        refresh_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Patients list
        patients_container = ttk.Frame(patients_frame)
        patients_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.patients_listbox = tk.Listbox(patients_container)
        self.patients_listbox.bind("<<ListboxSelect>>", self.update_patient_files)
        self.patients_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        patients_scrollbar = ttk.Scrollbar(patients_container, orient=tk.VERTICAL, command=self.patients_listbox.yview)
        patients_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.patients_listbox.config(yscrollcommand=patients_scrollbar.set)
        
        # Patient actions
        patient_actions = ttk.Frame(patients_frame)
        patient_actions.pack(fill=tk.X, padx=5, pady=5)
        
        view_button = ttk.Button(
            patient_actions,
            text="View Patient Details",
            command=self.view_patient_details
        )
        view_button.pack(side=tk.LEFT, padx=5)
        
        # Right side: Patient files
        files_frame = ttk.LabelFrame(main_container, text="Patient Files")
        files_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Files list
        files_container = ttk.Frame(files_frame)
        files_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.files_listbox = tk.Listbox(files_container)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_scrollbar = ttk.Scrollbar(files_container, orient=tk.VERTICAL, command=self.files_listbox.yview)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)
        
        # File actions
        file_actions = ttk.Frame(files_frame)
        file_actions.pack(fill=tk.X, padx=5, pady=5)
        
        view_file_button = ttk.Button(
            file_actions,
            text="View File",
            command=self.view_file
        )
        view_file_button.pack(side=tk.LEFT, padx=5)
        
        send_file_button = ttk.Button(
            file_actions,
            text="Send File to Patient",
            command=self.send_file
        )
        send_file_button.pack(side=tk.LEFT, padx=5)
        
        # Load initial data
        self.refresh_patients()
    
    def refresh_patients(self):
        """Refresh the list of patients"""
        self.patients_listbox.delete(0, tk.END)
        
        # In a real implementation, this would load from a database
        # For prototype, get patients from the credentials file
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
                patients = credentials.get("patients", {})
                
                self.all_patients = []
                
                for username, data in patients.items():
                    name = data.get("name", username)
                    display_name = f"{name} ({username})"
                    self.all_patients.append((username, display_name))
                    self.patients_listbox.insert(tk.END, display_name)
        
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    def update_patient_files(self, event=None):
        """Update files list based on selected patient"""
        self.files_listbox.delete(0, tk.END)
        
        selected = self.patients_listbox.curselection()
        if not selected:
            return
        
        # Get username from selected display name
        if not hasattr(self, 'all_patients') or len(self.all_patients) <= selected[0]:
            return
            
        username = self.all_patients[selected[0]][0]
        
        # Check patient files directory
        patient_files_dir = os.path.join(self.user_dir, "patient_files", username)
        if os.path.exists(patient_files_dir):
            for filename in os.listdir(patient_files_dir):
                file_path = os.path.join(patient_files_dir, filename)
                if os.path.isfile(file_path):
                    self.files_listbox.insert(tk.END, filename)
    
    def view_patient_details(self):
        """View details for the selected patient"""
        selected = self.patients_listbox.curselection()
        if not selected:
            messagebox.showinfo("Patient Selection", "Please select a patient")
            return
        
        if not hasattr(self, 'all_patients') or len(self.all_patients) <= selected[0]:
            return
            
        username = self.all_patients[selected[0]][0]
        
        # Get patient data
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
                patient_data = credentials.get("patients", {}).get(username)
                
                if patient_data:
                    # Create a popup window with patient details
                    details_window = tk.Toplevel(self)
                    details_window.title(f"Patient Details: {patient_data.get('name', username)}")
                    details_window.geometry("400x400")
                    
                    # Create scrollable frame
                    canvas = tk.Canvas(details_window)
                    scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=canvas.yview)
                    
                    details_frame = ttk.Frame(canvas)
                    details_frame.bind(
                        "<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                    )
                    
                    canvas.create_window((0, 0), window=details_frame, anchor="nw")
                    canvas.configure(yscrollcommand=scrollbar.set)
                    
                    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Display patient information
                    row = 0
                    
                    ttk.Label(details_frame, text="Basic Information", font=("Arial", 12, "bold")).grid(
                        row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5
                    )
                    row += 1
                    
                    fields = [
                        ("Name", "name"),
                        ("Age", "age"),
                        ("Gender", "gender"),
                        ("Email", "email"),
                        ("Phone", "phone")
                    ]
                    
                    for label, key in fields:
                        ttk.Label(details_frame, text=f"{label}:", font=("Arial", 10, "bold")).grid(
                            row=row, column=0, sticky=tk.W, padx=5, pady=2
                        )
                        ttk.Label(details_frame, text=patient_data.get(key, "")).grid(
                            row=row, column=1, sticky=tk.W, padx=5, pady=2
                        )
                        row += 1
                    
                    # Medical information
                    ttk.Separator(details_frame, orient=tk.HORIZONTAL).grid(
                        row=row, column=0, columnspan=2, sticky=tk.EW, pady=5
                    )
                    row += 1
                    
                    ttk.Label(details_frame, text="Medical Information", font=("Arial", 12, "bold")).grid(
                        row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5
                    )
                    row += 1
                    
                    ttk.Label(details_frame, text="Allergies:", font=("Arial", 10, "bold")).grid(
                        row=row, column=0, sticky=tk.NW, padx=5, pady=2
                    )
                    
                    allergies_text = tk.Text(details_frame, height=2, width=30, wrap=tk.WORD)
                    allergies_text.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    allergies_text.insert(tk.END, patient_data.get("allergies", "None reported"))
                    allergies_text.config(state=tk.DISABLED)
                    row += 1
                    
                    ttk.Label(details_frame, text="Medical History:", font=("Arial", 10, "bold")).grid(
                        row=row, column=0, sticky=tk.NW, padx=5, pady=2
                    )
                    
                    history_text = tk.Text(details_frame, height=6, width=30, wrap=tk.WORD)
                    history_text.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    history_text.insert(tk.END, patient_data.get("medical_history", "None reported"))
                    history_text.config(state=tk.DISABLED)
                    
                else:
                    messagebox.showerror("Patient Data", "Could not retrieve patient data")
        
        except (json.JSONDecodeError, FileNotFoundError):
            messagebox.showerror("Data Error", "Could not load patient data")
    
    def view_file(self):
        """View selected patient file"""
        selected_patient = self.patients_listbox.curselection()
        selected_file = self.files_listbox.curselection()
        
        if not selected_patient or not selected_file:
            messagebox.showinfo("Selection", "Please select a patient and a file")
            return
            
        if not hasattr(self, 'all_patients') or len(self.all_patients) <= selected_patient[0]:
            return
            
        username = self.all_patients[selected_patient[0]][0]
        filename = self.files_listbox.get(selected_file[0])
        
        # Get file path
        file_path = os.path.join(
            self.user_dir,
            "patient_files",
            username,
            filename
        )
        
        if os.path.exists(file_path):
            import platform
            import subprocess
            
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
    
    def send_file(self):
        """Send a file to the selected patient"""
        selected = self.patients_listbox.curselection()
        if not selected:
            messagebox.showinfo("Patient Selection", "Please select a patient")
            return
            
        if not hasattr(self, 'all_patients') or len(self.all_patients) <= selected[0]:
            return
            
        username = self.all_patients[selected[0]][0]
        display_name = self.patients_listbox.get(selected[0])
        
        file_path = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("Documents", "*.pdf *.docx *.txt"),
                ("Images", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.join(
            get_user_dir(username, "patient"),
            "doctor_files",
            self.user_data["username"]
        )
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy file
        try:
            import shutil
            filename = os.path.basename(file_path)
            dest_path = os.path.join(dest_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            
            messagebox.showinfo(
                "File Sent", 
                f"File has been sent to {display_name}"
            )
        except Exception as e:
            messagebox.showerror("File Error", f"Error sending file: {str(e)}")


class MessagingPanel(ttk.LabelFrame):
    """Messaging panel UI component"""
    
    def __init__(self, parent, user_data):
        super().__init__(parent, text="Patient Communication")
        
        self.user_data = user_data
        self.user_dir = get_user_dir(user_data["username"], "doctor")
        self.message_service = MessageService(user_data)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the messaging UI"""
        # Patient selector
        select_frame = ttk.Frame(self)
        select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(select_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        
        self.patient_var = tk.StringVar()
        self.patient_combo = ttk.Combobox(
            select_frame,
            textvariable=self.patient_var,
            width=20
        )
        self.patient_combo.pack(side=tk.LEFT, padx=5)
        self.patient_combo.bind("<<ComboboxSelected>>", self.load_conversation)
        
        refresh_button = ttk.Button(
            select_frame,
            text="🔄",
            command=self.load_patients,
            width=3
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Message display
        self.messages_text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.messages_text.tag_configure("sent", foreground="#0066cc")
        self.messages_text.tag_configure("received", foreground="#006633")
        self.messages_text.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
        self.messages_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        send_button.pack(side=tk.LEFT, padx=5)
        
        send_file_button = ttk.Button(
            input_frame,
            text="Send File",
            command=self.send_file
        )
        send_file_button.pack(side=tk.LEFT, padx=5)
        
        # Load patients
        self.load_patients()
    
    def load_patients(self):
        """Load list of patients from credentials"""
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
                patients = credentials.get("patients", {})
                
                patient_names = []
                self.patient_usernames = {}
                
                for username, data in patients.items():
                    name = data.get("name", username)
                    display_name = f"{name} ({username})"
                    patient_names.append(display_name)
                    self.patient_usernames[display_name] = username
                
                self.patient_combo['values'] = patient_names
                
                # Also check for existing conversations
                conversations = self.message_service.get_all_conversations()
                if conversations:
                    # Pre-select the first patient with an existing conversation
                    for display_name, username in self.patient_usernames.items():
                        if username in conversations:
                            self.patient_combo.set(display_name)
                            self.load_conversation()
                            break
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    def load_conversation(self, event=None):
        """Load conversation with selected patient"""
        selected_patient = self.patient_var.get()
        if not selected_patient or not hasattr(self, 'patient_usernames'):
            print("No patient selected or patient_usernames dictionary not available")
            return
        
        if selected_patient not in self.patient_usernames:
            print(f"Selected patient {selected_patient} not found in patient_usernames dictionary")
            return
        
        patient_username = self.patient_usernames[selected_patient]
        print(f"Loading conversation with patient {patient_username}")
        
        # Get conversation history
        conversation = self.message_service.get_conversation(patient_username)
        print(f"Found {len(conversation)} messages in conversation")
        
        # Display conversation
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        
        if not conversation:
            self.messages_text.insert(tk.END, "No previous messages with this patient.\n", "system")
        else:
            for message in conversation:
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                sender = message["sender_username"]
                content = message["content"]
                
                if sender == self.user_data["username"]:
                    # Message sent by the doctor
                    self.messages_text.insert(tk.END, f"[{timestamp}] You: {content}\n\n", "sent")
                else:
                    # Message received from the patient
                    patient_name = selected_patient.split(" (")[0]
                    self.messages_text.insert(tk.END, f"[{timestamp}] {patient_name}: {content}\n\n", "received")
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def send_message(self):
        """Send a message to a patient"""
        patient = self.patient_var.get()
        message = self.message_entry.get().strip()
        
        if not patient:
            messagebox.showwarning("Patient Selection", "Please select a patient")
            return
        
        if not message:
            return
        
        if not hasattr(self, 'patient_usernames') or patient not in self.patient_usernames:
            messagebox.showwarning("Patient Selection", "Invalid patient selection")
            return
        
        # Get patient username
        patient_username = self.patient_usernames[patient]
        
        # Send the message
        success = self.message_service.send_message(
            patient_username,
            "patient",
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
    
    def send_file(self):
        """Send a file to the selected patient"""
        patient = self.patient_var.get()
        
        if not patient:
            messagebox.showwarning("Patient Selection", "Please select a patient")
            return
        
        if not hasattr(self, 'patient_usernames') or patient not in self.patient_usernames:
            messagebox.showwarning("Patient Selection", "Invalid patient selection")
            return
        
        # Extract username
        patient_username = self.patient_usernames[patient]
        
        file_path = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("Documents", "*.pdf *.docx *.txt"),
                ("Images", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.join(
            get_user_dir(patient_username, "patient"),
            "doctor_files",
            self.user_data["username"]
        )
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy file
        try:
            import shutil
            filename = os.path.basename(file_path)
            dest_path = os.path.join(dest_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            
            # Add notification to messages
            self.messages_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.messages_text.insert(tk.END, f"[{timestamp}] You sent file: {filename}\n\n", "system")
            self.messages_text.see(tk.END)
            self.messages_text.config(state=tk.DISABLED)
            
            # Also add a message in the conversation
            self.message_service.send_message(
                patient_username,
                "patient",
                f"[File sent: {filename}]"
            )
            
            messagebox.showinfo(
                "File Sent", 
                f"File has been sent to {patient}"
            )
        except Exception as e:
            messagebox.showerror("File Error", f"Error sending file: {str(e)}")


class MedicalAdvisorPanel(ttk.LabelFrame):
    """Medical advisor panel UI component"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Medical Reference")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the medical advisor UI"""
        # Search bar
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.bind("<Return>", lambda e: self.search_reference())
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        search_button = ttk.Button(
            search_frame,
            text="Search",
            command=self.search_reference
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Categories
        categories_frame = ttk.Frame(self)
        categories_frame.pack(fill=tk.X, padx=10, pady=5)
        
        categories = ["Medications", "Conditions", "Procedures", "Guidelines"]
        
        for category in categories:
            ttk.Button(
                categories_frame,
                text=category,
                command=lambda c=category: self.show_category(c)
            ).pack(side=tk.LEFT, padx=5)
        
        # Reference content
        self.content_text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show default content
        self.show_welcome()
    
    def search_reference(self):
        """Search medical references"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showinfo("Search", "Please enter a search term")
            return
        
        # In a real implementation, this would search a medical database
        # For prototype, show a placeholder
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        self.content_text.insert(tk.END, f"Search Results for '{query}'\n\n", "heading")
        self.content_text.insert(tk.END, "This is a prototype. In the final implementation, this would search a medical reference database and return relevant information.\n\n")
        self.content_text.insert(tk.END, "Example results:\n\n")
        
        # Generate some placeholder results based on the query
        self.content_text.insert(tk.END, f"1. Understanding {query.title()}: Clinical Overview\n", "result")
        self.content_text.insert(tk.END, f"   Summary of {query.lower()} including definitions, causes, and treatments.\n\n")
        
        self.content_text.insert(tk.END, f"2. Latest Research on {query.title()}\n", "result")
        self.content_text.insert(tk.END, f"   Recent studies and findings related to {query.lower()}.\n\n")
        
        self.content_text.insert(tk.END, f"3. Treatment Guidelines for {query.title()}\n", "result")
        self.content_text.insert(tk.END, f"   Standard protocols and best practices for managing {query.lower()}.\n\n")
        
        self.content_text.config(state=tk.DISABLED)
    
    def show_category(self, category):
        """Show reference materials for a specific category"""
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        self.content_text.insert(tk.END, f"{category} Reference\n\n", "heading")
        self.content_text.insert(tk.END, "This is a prototype. In the final implementation, this would display reference materials for the selected category.\n\n")
        
        # Show different placeholder content based on category
        if category == "Medications":
            self.content_text.insert(tk.END, "Medication Database\n\n")
            self.content_text.insert(tk.END, "- Common medications by class\n")
            self.content_text.insert(tk.END, "- Dosing guidelines\n")
            self.content_text.insert(tk.END, "- Side effects and interactions\n")
            self.content_text.insert(tk.END, "- Contraindications\n")
            
        elif category == "Conditions":
            self.content_text.insert(tk.END, "Medical Conditions Reference\n\n")
            self.content_text.insert(tk.END, "- Disease pathophysiology\n")
            self.content_text.insert(tk.END, "- Diagnostic criteria\n")
            self.content_text.insert(tk.END, "- Clinical presentations\n")
            self.content_text.insert(tk.END, "- Treatment approaches\n")
            
        elif category == "Procedures":
            self.content_text.insert(tk.END, "Clinical Procedures Guide\n\n")
            self.content_text.insert(tk.END, "- Common medical procedures\n")
            self.content_text.insert(tk.END, "- Indications and contraindications\n")
            self.content_text.insert(tk.END, "- Technique and best practices\n")
            self.content_text.insert(tk.END, "- Post-procedure care\n")
            
        elif category == "Guidelines":
            self.content_text.insert(tk.END, "Clinical Practice Guidelines\n\n")
            self.content_text.insert(tk.END, "- Evidence-based recommendations\n")
            self.content_text.insert(tk.END, "- Specialty-specific guidelines\n")
            self.content_text.insert(tk.END, "- Screening and prevention\n")
            self.content_text.insert(tk.END, "- Quality measures\n")
        
        self.content_text.config(state=tk.DISABLED)
    
    def show_welcome(self):
        """Show the welcome page"""
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        self.content_text.insert(tk.END, "Medical Reference Library\n\n", "heading")
        self.content_text.insert(tk.END, "Welcome to the medical reference section. This tool provides quick access to medical information to support clinical decision-making.\n\n")
        self.content_text.insert(tk.END, "Features:\n\n")
        self.content_text.insert(tk.END, "- Search for specific medical topics\n")
        self.content_text.insert(tk.END, "- Browse by category (Medications, Conditions, Procedures, Guidelines)\n")
        self.content_text.insert(tk.END, "- Access evidence-based clinical content\n\n")
        self.content_text.insert(tk.END, "Note: This is a prototype. In the final implementation, this would connect to a comprehensive medical reference database.\n")
        
        self.content_text.config(state=tk.DISABLED)


class DoctorView(ttk.Frame):
    """Main view for doctor interactions - Updated layout"""
    
    def __init__(self, parent, user_data, app):
        super().__init__(parent)
        self.user_data = user_data
        self.app = app
        self.user_dir = get_user_dir(user_data["username"], "doctor")
        
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
        """Set up the doctor interface with the new layout"""
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
        
        # Left side: Patient Management (top) and AI Assistant (bottom)
        # Patient Management Panel
        self.patient_panel = PatientManagementPanel(
            content_frame,
            self.user_data
        )
        self.patient_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # AI Medical Assistant Chat
        self.chat_panel = ChatPanel(
            content_frame, 
            self.chat_controller, 
            self.speech_service,
            self.message_queue
        )
        self.chat_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Right side: Document panel (top) and Messaging (bottom)
        # Document panel (upper right)
        self.document_panel = DocumentPanel(
            content_frame, 
            self.document_controller,
            self.message_queue
        )
        self.document_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Right bottom: Notebook with Messaging and Medical Reference
        right_bottom = ttk.Notebook(content_frame)
        right_bottom.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Add Messaging tab
        self.messaging_panel = MessagingPanel(
            right_bottom,
            self.user_data
        )
        right_bottom.add(self.messaging_panel, text="Patient Communication")
        
        # Add Medical Advisor tab
        self.advisor_panel = MedicalAdvisorPanel(right_bottom)
        right_bottom.add(self.advisor_panel, text="Medical Reference")
        
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
            text="Doctor Profile", 
            font=("Arial", 12, "bold"),
            padding=(5, 5, 5, 5)
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Basic info layout
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Create a grid of labels for doctor information
        labels = [
            ("Name:", self.user_data.get("name", "")),
            ("Specialization:", self.user_data.get("specialization", "")),
            ("License:", self.user_data.get("license", "")),
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
                        pass
                
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