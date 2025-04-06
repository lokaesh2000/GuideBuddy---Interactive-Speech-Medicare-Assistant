"""
Document Panel Component
Reusable UI component for document upload and management
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

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