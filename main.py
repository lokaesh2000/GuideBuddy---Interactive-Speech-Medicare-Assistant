#!/usr/bin/env python3
"""
GuideAI - Medical Assistant Application
Main entry point for the GuideAI application
"""

import os
import tkinter as tk
from tkinter import ttk
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.auth_view import AuthView
from controllers.auth_controller import AuthController
from config.settings import initialize_app_directories

class GuideAI(tk.Tk):
    """Main application class for GuideAI"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize application directories
        initialize_app_directories()
        
        # Configure the main window
        self.title("GuideAI - Medical Assistant")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Set up theme
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Using clam theme for modern look
        
        # Configure styles
        self.configure_styles()
        
        # Set up the container frame for all views
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize controllers
        self.auth_controller = AuthController(self)
        
        # Show the authentication view (login/signup)
        self.current_view = None
        self.show_auth_view()
    
    def configure_styles(self):
        """Configure ttk styles for the application"""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 11))
        self.style.configure('TLabel', font=('Arial', 11), background='#f0f0f0')
        self.style.configure('TEntry', font=('Arial', 11))
        
        # Custom styles
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        self.style.configure('Primary.TButton', background='#4a86e8', foreground='white')
    
    def show_auth_view(self):
        """Display the authentication view (login/signup)"""
        if self.current_view:
            self.current_view.destroy()
        
        self.current_view = AuthView(self.container, self.auth_controller)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    def show_patient_view(self, user_data):
        """Switch to the patient main interface"""
        from views.patient_view import PatientView
        
        if self.current_view:
            self.current_view.destroy()
        
        self.current_view = PatientView(self.container, user_data, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    def show_doctor_view(self, user_data):
        """Switch to the doctor main interface"""
        from views.doctor_view import DoctorView
        
        if self.current_view:
            self.current_view.destroy()
        
        self.current_view = DoctorView(self.container, user_data, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = GuideAI()
    app.mainloop()