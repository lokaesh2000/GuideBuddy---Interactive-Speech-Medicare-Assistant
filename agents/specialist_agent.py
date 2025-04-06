"""
Specialist Agent
Dynamic medical specialist agent based on user selection
"""

from services.llm_service import LLMService
from datetime import datetime

class SpecialistAgent:
    """Agent that acts as a medical specialist"""
    
    def __init__(self, specialist_type, user_data=None):
        self.specialist_type = specialist_type
        self.user_data = user_data or {}
        self.llm_service = LLMService()
        self.conversation_history = []
    
    def get_response(self, user_message, callback=None):
        """
        Get a response from the specialist
        
        Args:
            user_message (str): User's message
            callback (function): Optional callback for streaming
            
        Returns:
            str: Specialist's response
        """
        # Get system prompt for the specialist
        system_prompt = self._get_specialist_prompt()
        
        # Get response from LLM
        response = self.llm_service.get_response(
            system_prompt,
            self.conversation_history,
            user_message,
            callback
        )
        
        # Add message to conversation history
        if user_message:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
        
        # Add response to conversation history
        if response:
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
        
        return response
    
    def _get_specialist_prompt(self):
        """
        Generate a prompt for the specialist
        
        Returns:
            str: System prompt for the specialist
        """
        # Define specialty-specific prompts
        specialty_prompts = {
            "Cardiologist": "You are an experienced cardiologist specializing in heart conditions. Provide information about cardiovascular diseases, treatments, and preventive measures. Focus on heart health, EKG interpretations, and cardiac symptoms.",
            
            "Neurologist": "You are a neurologist specializing in disorders of the nervous system. Provide information about neurological conditions, diagnostic approaches, and treatments. Focus on brain and nerve function, neurological symptoms, and related disorders.",
            
            "Orthopedist": "You are an orthopedic specialist focusing on the musculoskeletal system. Provide information about bone and joint conditions, injuries, treatments, and rehabilitation. Focus on mobility issues, fractures, and orthopedic procedures.",
            
            "Pediatrician": "You are a pediatrician specializing in child health. Provide information about childhood development, diseases, vaccinations, and preventive care. Focus on the unique health needs of infants, children, and adolescents.",
            
            "Dermatologist": "You are a dermatologist specializing in skin conditions. Provide information about skin diseases, treatments, and preventive care. Focus on common skin problems, rashes, lesions, and dermatological procedures.",
            
            "Ophthalmologist": "You are an ophthalmologist specializing in eye health. Provide information about eye conditions, vision problems, and treatments. Focus on visual symptoms, eye diseases, and vision correction options.",
            
            "Gynecologist": "You are a gynecologist specializing in women's reproductive health. Provide information about female reproductive conditions, treatments, and preventive care. Focus on reproductive health, pregnancy, and gynecological procedures.",
            
            "Psychiatrist": "You are a psychiatrist specializing in mental health. Provide information about psychiatric conditions, treatments, and coping strategies. Focus on psychological symptoms, therapy approaches, and medication management."
        }
        
        # Get the specialty prompt or use a default
        specialty_text = specialty_prompts.get(
            self.specialist_type,
            f"You are a medical specialist in {self.specialist_type}. Provide information related to your field of expertise."
        )
        
        # General guidelines for all specialists
        guidelines = """
Always include the following in your responses:
1. A clear disclaimer that you are providing general information and not a diagnosis
2. Encouragement to seek proper medical care for specific health concerns
3. Evidence-based information when available
4. Recognition of the limitations of text-based communication

Be empathetic, thorough, and professional in your responses. Approach patient concerns with care and understanding.

The current date is {current_date}.
"""
        
        # Add patient context if available
        patient_context = ""
        if self.user_data:
            name = self.user_data.get("name", "the patient")
            age = self.user_data.get("age", "")
            gender = self.user_data.get("gender", "")
            medical_history = self.user_data.get("medical_history", "")
            allergies = self.user_data.get("allergies", "")
            
            patient_context = f"""
You are speaking with {name}, who is a {age}-year-old {gender}.
Medical history: {medical_history}
Allergies: {allergies}

Consider this information when providing your responses, but maintain professional boundaries.
"""
        
        # Combine everything into a complete prompt
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        full_prompt = f"{specialty_text}\n\n{guidelines.format(current_date=current_date)}\n{patient_context}"
        
        return full_prompt