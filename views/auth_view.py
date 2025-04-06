"""
Authentication View
Provides login and signup interfaces
"""

import tkinter as tk
from tkinter import ttk, messagebox

class AuthView(ttk.Frame):
    """View for handling user authentication (login/signup)"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.current_frame = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the authentication UI"""
        # Create a notebook with tabs for login and signup
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create login frame
        self.login_frame = ttk.Frame(self.notebook)
        self.setup_login_frame()
        self.notebook.add(self.login_frame, text="Login")
        
        # Create signup frame
        self.signup_frame = ttk.Frame(self.notebook)
        self.setup_signup_frame()
        self.notebook.add(self.signup_frame, text="Sign Up")
    
    def setup_login_frame(self):
        """Set up the login form"""
        # Create a frame to center the login form
        center_frame = ttk.Frame(self.login_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        ttk.Label(center_frame, text="Login to GuideAI", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=20)
        
        # Username
        ttk.Label(center_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.login_username = ttk.Entry(center_frame, width=30)
        self.login_username.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Password
        ttk.Label(center_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.login_password = ttk.Entry(center_frame, width=30, show="*")
        self.login_password.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # User type radio buttons
        self.login_user_type = tk.StringVar(value="patient")
        ttk.Label(center_frame, text="I am a:").grid(row=3, column=0, sticky=tk.W, pady=5)
        user_type_frame = ttk.Frame(center_frame)
        user_type_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(user_type_frame, text="Patient", variable=self.login_user_type, value="patient").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(user_type_frame, text="Doctor", variable=self.login_user_type, value="doctor").pack(side=tk.LEFT, padx=5)
        
        # Login button
        login_button = ttk.Button(center_frame, text="Login", command=self.handle_login)
        login_button.grid(row=4, column=0, columnspan=2, pady=20)
    
    def setup_signup_frame(self):
        """Set up the signup form"""
        # Create a frame with scrollbar
        main_frame = ttk.Frame(self.signup_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        ttk.Label(scrollable_frame, text="Create a New Account", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        
        # User type selection
        self.signup_user_type = tk.StringVar(value="patient")
        ttk.Label(scrollable_frame, text="I am a:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=20)
        user_type_frame = ttk.Frame(scrollable_frame)
        user_type_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(user_type_frame, text="Patient", variable=self.signup_user_type, value="patient", command=self.toggle_signup_fields).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(user_type_frame, text="Doctor", variable=self.signup_user_type, value="doctor", command=self.toggle_signup_fields).pack(side=tk.LEFT, padx=5)
        
        # Username
        ttk.Label(scrollable_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_username = ttk.Entry(scrollable_frame, width=30)
        self.signup_username.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Password
        ttk.Label(scrollable_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_password = ttk.Entry(scrollable_frame, width=30, show="*")
        self.signup_password.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Confirm Password
        ttk.Label(scrollable_frame, text="Confirm Password:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_confirm_password = ttk.Entry(scrollable_frame, width=30, show="*")
        self.signup_confirm_password.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Common user information
        ttk.Label(scrollable_frame, text="Full Name:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_name = ttk.Entry(scrollable_frame, width=30)
        self.signup_name.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(scrollable_frame, text="Age:").grid(row=6, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_age = ttk.Entry(scrollable_frame, width=30)
        self.signup_age.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(scrollable_frame, text="Gender:").grid(row=7, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_gender = ttk.Combobox(scrollable_frame, values=["Male", "Female", "Other"], width=27)
        self.signup_gender.grid(row=7, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(scrollable_frame, text="Email:").grid(row=8, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_email = ttk.Entry(scrollable_frame, width=30)
        self.signup_email.grid(row=8, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(scrollable_frame, text="Phone:").grid(row=9, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_phone = ttk.Entry(scrollable_frame, width=30)
        self.signup_phone.grid(row=9, column=1, sticky=tk.W, pady=5)
        
        # Patient-specific fields (hidden for doctors)
        self.patient_frame = ttk.Frame(scrollable_frame)
        self.patient_frame.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(self.patient_frame, text="Medical History:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_medical_history = tk.Text(self.patient_frame, width=30, height=4)
        self.signup_medical_history.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.patient_frame, text="Allergies:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_allergies = ttk.Entry(self.patient_frame, width=30)
        self.signup_allergies.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Doctor-specific fields (hidden for patients)
        self.doctor_frame = ttk.Frame(scrollable_frame)
        self.doctor_frame.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(self.doctor_frame, text="Specialization:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_specialization = ttk.Entry(self.doctor_frame, width=30)
        self.signup_specialization.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.doctor_frame, text="License Number:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=20)
        self.signup_license = ttk.Entry(self.doctor_frame, width=30)
        self.signup_license.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Toggle fields based on initial user type
        self.toggle_signup_fields()
        
        # Sign up button
        signup_button = ttk.Button(scrollable_frame, text="Sign Up", command=self.handle_signup)
        signup_button.grid(row=11, column=0, columnspan=2, pady=20)
    
    def toggle_signup_fields(self):
        """Toggle visibility of fields based on user type"""
        if self.signup_user_type.get() == "patient":
            self.patient_frame.grid()
            self.doctor_frame.grid_remove()
        else:
            self.patient_frame.grid_remove()
            self.doctor_frame.grid()
    
    def handle_login(self):
        """Handle login button click"""
        username = self.login_username.get()
        password = self.login_password.get()
        user_type = self.login_user_type.get()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password")
            return
        
        success = self.controller.authenticate_and_redirect(username, password, user_type)
        
        if not success:
            messagebox.showerror("Login Error", "Invalid username or password")
    
    def handle_signup(self):
        """Handle signup button click"""
        # Get basic information
        username = self.signup_username.get()
        password = self.signup_password.get()
        confirm_password = self.signup_confirm_password.get()
        user_type = self.signup_user_type.get()
        
        # Validate required fields
        if not username or not password or not confirm_password:
            messagebox.showerror("Signup Error", "Please fill in all required fields")
            return
        
        # Validate password confirmation
        if password != confirm_password:
            messagebox.showerror("Signup Error", "Passwords do not match")
            return
        
        # Common user data
        user_data = {
            "name": self.signup_name.get(),
            "age": self.signup_age.get(),
            "gender": self.signup_gender.get(),
            "email": self.signup_email.get(),
            "phone": self.signup_phone.get(),
        }
        
        # Add type-specific data
        if user_type == "patient":
            user_data.update({
                "medical_history": self.signup_medical_history.get("1.0", tk.END).strip(),
                "allergies": self.signup_allergies.get(),
            })
        else:
            user_data.update({
                "specialization": self.signup_specialization.get(),
                "license": self.signup_license.get(),
            })
        
        # Register the user
        result = self.controller.register(username, password, user_data, user_type)
        
        if result:
            messagebox.showinfo("Success", "Account created successfully")
            self.controller.authenticate_and_redirect(username, password, user_type)
        else:
            messagebox.showerror("Signup Error", "Username already exists")