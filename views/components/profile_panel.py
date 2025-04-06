"""
Profile Panel Component
Reusable UI component for displaying user profile information
"""

import tkinter as tk
from tkinter import ttk

class ProfilePanel(ttk.LabelFrame):
    """Profile panel UI component"""
    
    def __init__(self, parent, user_data):
        super().__init__(parent, text="Patient Profile")
        
        self.user_data = user_data
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the profile UI"""
        # Main container with scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        self.profile_frame = ttk.Frame(canvas)
        self.profile_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.profile_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add profile data
        self.display_profile()
    
    def display_profile(self):
        """Display the user profile data"""
        # Name and basic info
        ttk.Label(self.profile_frame, text="Name:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(self.profile_frame, text=self.user_data.get("name", "")).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        ttk.Label(self.profile_frame, text="Age:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(self.profile_frame, text=self.user_data.get("age", "")).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        ttk.Label(self.profile_frame, text="Gender:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(self.profile_frame, text=self.user_data.get("gender", "")).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        # Contact information
        ttk.Separator(self.profile_frame, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=2, sticky=tk.EW, pady=5
        )
        
        ttk.Label(self.profile_frame, text="Contact Information", font=("Arial", 10, "bold")).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2
        )
        
        ttk.Label(self.profile_frame, text="Email:", font=("Arial", 10, "bold")).grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(self.profile_frame, text=self.user_data.get("email", "")).grid(
            row=5, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        ttk.Label(self.profile_frame, text="Phone:", font=("Arial", 10, "bold")).grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(self.profile_frame, text=self.user_data.get("phone", "")).grid(
            row=6, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        # Medical information (for patients only)
        if self.user_data.get("user_type") == "patient":
            ttk.Separator(self.profile_frame, orient=tk.HORIZONTAL).grid(
                row=7, column=0, columnspan=2, sticky=tk.EW, pady=5
            )
            
            ttk.Label(self.profile_frame, text="Medical Information", font=("Arial", 10, "bold")).grid(
                row=8, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(self.profile_frame, text="Allergies:", font=("Arial", 10, "bold")).grid(
                row=9, column=0, sticky=tk.NW, padx=5, pady=2
            )
            
            allergies_text = tk.Text(self.profile_frame, height=2, width=30, wrap=tk.WORD)
            allergies_text.grid(row=9, column=1, sticky=tk.W, padx=5, pady=2)
            allergies_text.insert(tk.END, self.user_data.get("allergies", "None reported"))
            allergies_text.config(state=tk.DISABLED)
            
            ttk.Label(self.profile_frame, text="Medical History:", font=("Arial", 10, "bold")).grid(
                row=10, column=0, sticky=tk.NW, padx=5, pady=2
            )
            
            history_text = tk.Text(self.profile_frame, height=6, width=30, wrap=tk.WORD)
            history_text.grid(row=10, column=1, sticky=tk.W, padx=5, pady=2)
            history_text.insert(tk.END, self.user_data.get("medical_history", "None reported"))
            history_text.config(state=tk.DISABLED)
        
        # Professional information (for doctors only)
        elif self.user_data.get("user_type") == "doctor":
            ttk.Separator(self.profile_frame, orient=tk.HORIZONTAL).grid(
                row=7, column=0, columnspan=2, sticky=tk.EW, pady=5
            )
            
            ttk.Label(self.profile_frame, text="Professional Information", font=("Arial", 10, "bold")).grid(
                row=8, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(self.profile_frame, text="Specialization:", font=("Arial", 10, "bold")).grid(
                row=9, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(self.profile_frame, text=self.user_data.get("specialization", "")).grid(
                row=9, column=1, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(self.profile_frame, text="License:", font=("Arial", 10, "bold")).grid(
                row=10, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(self.profile_frame, text=self.user_data.get("license", "")).grid(
                row=10, column=1, sticky=tk.W, padx=5, pady=2
            )