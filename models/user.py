"""
User Models
Classes for Patient and Doctor users
"""

class User:
    """Base user class with common attributes"""
    
    def __init__(self, username, name, age, gender, email, phone):
        self.username = username
        self.name = name
        self.age = age
        self.gender = gender
        self.email = email
        self.phone = phone
    
    @classmethod
    def from_dict(cls, data):
        """Create a user instance from a dictionary"""
        return cls(**data)
    
    def to_dict(self):
        """Convert user to dictionary representation"""
        return {
            "username": self.username,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "email": self.email,
            "phone": self.phone
        }


class Patient(User):
    """Patient user model with medical information"""
    
    def __init__(self, username, name, age, gender, email, phone, medical_history=None, allergies=None):
        super().__init__(username, name, age, gender, email, phone)
        self.medical_history = medical_history or ""
        self.allergies = allergies or ""
        self.user_type = "patient"
    
    @classmethod
    def from_dict(cls, data):
        """Create a patient instance from a dictionary"""
        return cls(
            username=data.get("username", ""),
            name=data.get("name", ""),
            age=data.get("age", ""),
            gender=data.get("gender", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            medical_history=data.get("medical_history", ""),
            allergies=data.get("allergies", "")
        )
    
    def to_dict(self):
        """Convert patient to dictionary representation"""
        data = super().to_dict()
        data.update({
            "medical_history": self.medical_history,
            "allergies": self.allergies,
            "user_type": self.user_type
        })
        return data


class Doctor(User):
    """Doctor user model with professional information"""
    
    def __init__(self, username, name, age, gender, email, phone, specialization=None, license=None):
        super().__init__(username, name, age, gender, email, phone)
        self.specialization = specialization or ""
        self.license = license or ""
        self.user_type = "doctor"
    
    @classmethod
    def from_dict(cls, data):
        """Create a doctor instance from a dictionary"""
        return cls(
            username=data.get("username", ""),
            name=data.get("name", ""),
            age=data.get("age", ""),
            gender=data.get("gender", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            specialization=data.get("specialization", ""),
            license=data.get("license", "")
        )
    
    def to_dict(self):
        """Convert doctor to dictionary representation"""
        data = super().to_dict()
        data.update({
            "specialization": self.specialization,
            "license": self.license,
            "user_type": self.user_type
        })
        return data