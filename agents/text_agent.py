"""
Text Agent
Agent for processing text-based medical documents
"""

import os
import re
import PyPDF2
from services.llm_service import LLMService

class TextAgent:
    """Agent for processing text-based documents"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def process_document(self, document_path):
        """
        Process a text document
        
        Args:
            document_path (str): Path to the document
            
        Returns:
            str: Extracted and analyzed information
        """
        # Extract text from the document
        document_text = self._extract_text(document_path)
        
        # If no text could be extracted, return error
        if not document_text:
            return "Could not extract text from document."
        
        # Analyze text with LLM
        analysis = self._analyze_text(document_text)
        
        return analysis
    
    def _extract_text(self, document_path):
        """
        Extract text from a document
        
        Args:
            document_path (str): Path to the document
            
        Returns:
            str: Extracted text
        """
        # Get file extension
        _, ext = os.path.splitext(document_path)
        ext = ext.lower()
        
        try:
            # PDF files
            if ext == '.pdf':
                return self._extract_from_pdf(document_path)
            
            # Text files
            elif ext in ['.txt', '.text']:
                with open(document_path, 'r', errors='ignore') as f:
                    return f.read()
            
            # Word documents would need additional libraries
            # For prototype, we'll return a message
            elif ext in ['.docx', '.doc']:
                return "[This is a prototype. Word document processing would be implemented with python-docx library.]"
            
            # Default case - try to read as text
            else:
                try:
                    with open(document_path, 'r', errors='ignore') as f:
                        return f.read()
                except Exception:
                    return "Unsupported document format."
        
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def _extract_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        text = ""
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            
            return text
        
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    def _analyze_text(self, text):
        """
        Analyze medical text with LLM
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Analysis results
        """
        # Limit text length to avoid token limits
        max_chars = 5000  # Adjust based on model's token limit
        if len(text) > max_chars:
            analysis_text = text[:max_chars] + "...[truncated]"
        else:
            analysis_text = text
        
        # Create prompt for LLM
        prompt = f"""Analyze this medical document and extract key information:
- Patient information
- Diagnoses
- Medications and dosages
- Lab values and test results
- Treatment recommendations
- Follow-up instructions

Format the results in a structured, readable way.

Document text:
{analysis_text}
"""
        
        # Get analysis from LLM
        system_prompt = """You are a medical document analysis assistant. 
Your task is to extract and organize key information from medical documents.
Focus on facts and clinical details rather than interpretation.
Format your response in a clear, structured way with headings and bullet points."""
        
        # For prototype, simulate analysis if LLM API is not configured
        if not self.llm_service.api_key:
            return self._simulate_analysis(text)
        
        # Get real analysis from LLM
        analysis = self.llm_service.get_response_sync(system_prompt, [], prompt)
        return analysis
    
    def _simulate_analysis(self, text):
        """
        Simulate document analysis for prototype
        
        Args:
            text (str): Document text
            
        Returns:
            str: Simulated analysis
        """
        # Create a simple simulated analysis
        analysis = "DOCUMENT ANALYSIS\n\n"
        
        # Try to extract some common medical information with regex
        
        # Patient information
        patient_name_match = re.search(r"Patient:?\s*([A-Za-z\s]+)", text)
        patient_name = patient_name_match.group(1) if patient_name_match else "Not found"
        
        dob_match = re.search(r"DOB:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
        dob = dob_match.group(1) if dob_match else "Not found"
        
        # Add patient info
        analysis += "PATIENT INFORMATION:\n"
        analysis += f"- Name: {patient_name}\n"
        analysis += f"- DOB: {dob}\n\n"
        
        # Diagnoses
        analysis += "DIAGNOSES:\n"
        diagnosis_match = re.search(r"Diagnosis:?\s*([^\n]+)", text)
        if diagnosis_match:
            analysis += f"- {diagnosis_match.group(1)}\n\n"
        else:
            analysis += "- No clear diagnoses found\n\n"
        
        # Medications
        analysis += "MEDICATIONS:\n"
        med_matches = re.finditer(r"(\w+)\s+(\d+\s*mg)", text)
        meds_found = False
        
        for match in med_matches:
            analysis += f"- {match.group(1)}: {match.group(2)}\n"
            meds_found = True
        
        if not meds_found:
            analysis += "- No medications clearly identified\n"
        
        analysis += "\n"
        
        # Add disclaimer
        analysis += "NOTE: This is a simulated analysis for prototype purposes. In the final implementation, this would use the Gemini LLM for comprehensive analysis."
        
        return analysis