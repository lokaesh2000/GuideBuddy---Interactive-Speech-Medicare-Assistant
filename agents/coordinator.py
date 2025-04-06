"""
Coordinator Agent
Central agent that orchestrates document analysis
"""

import os
import mimetypes
from agents.text_agent import TextAgent
from agents.image_agent import ImageAgent
from agents.structured_agent import StructuredAgent

class CoordinatorAgent:
    """Coordinator agent for document analysis"""
    
    def __init__(self):
        # Initialize specialist agents
        self.text_agent = TextAgent()
        self.image_agent = ImageAgent()
        self.structured_agent = StructuredAgent()
    
    def analyze_documents(self, document_paths, callback=None):
        """
        Analyze a set of documents
        
        Args:
            document_paths (list): List of document paths
            callback (function): Optional callback for progress updates
            
        Returns:
            dict: Analysis results
        """
        if callback:
            callback("status", "Analyzing documents...")
        
        results = {
            "documents": [],
            "summary": "",
            "recommendations": ""
        }
        
        # Process each document with the appropriate agent
        for i, doc_path in enumerate(document_paths):
            if callback:
                callback("status", f"Processing document {i+1} of {len(document_paths)}...")
            
            # Determine document type
            doc_type = self._determine_document_type(doc_path)
            
            # Process with appropriate agent
            doc_result = self._process_with_agent(doc_path, doc_type, callback)
            
            # Add to results
            if doc_result:
                results["documents"].append({
                    "filename": os.path.basename(doc_path),
                    "type": doc_type,
                    "content": doc_result
                })
        
        # Generate summary and recommendations
        if callback:
            callback("status", "Generating summary and recommendations...")
        
        results["summary"] = self._generate_summary(results["documents"])
        results["recommendations"] = self._generate_recommendations(results["documents"])
        
        return results
    
    def _determine_document_type(self, document_path):
        """
        Determine the type of document based on file extension and mime type
        
        Args:
            document_path (str): Path to the document
            
        Returns:
            str: Document type ('text', 'image', 'structured', or 'unknown')
        """
        # Get file extension
        _, ext = os.path.splitext(document_path)
        ext = ext.lower()
        
        # Check mime type
        mime_type, _ = mimetypes.guess_type(document_path)
        
        # Determine type based on extension and mime type
        if ext in ['.pdf', '.txt', '.docx', '.doc', '.rtf']:
            return 'text'
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
            return 'image'
        elif ext in ['.csv', '.xls', '.xlsx']:
            return 'structured'
        elif mime_type:
            if mime_type.startswith('text/'):
                return 'text'
            elif mime_type.startswith('image/'):
                return 'image'
            elif mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                return 'structured'
        
        # Default to text for unknown types
        return 'text'
    
    def _process_with_agent(self, document_path, document_type, callback=None):
        """
        Process a document with the appropriate agent
        
        Args:
            document_path (str): Path to the document
            document_type (str): Type of document
            callback (function): Optional callback for progress updates
            
        Returns:
            str: Processing result
        """
        try:
            if document_type == 'text':
                if callback:
                    callback("status", "Processing text document...")
                return self.text_agent.process_document(document_path)
            
            elif document_type == 'image':
                if callback:
                    callback("status", "Processing image document...")
                return self.image_agent.process_document(document_path)
            
            elif document_type == 'structured':
                if callback:
                    callback("status", "Processing structured document...")
                return self.structured_agent.process_document(document_path)
            
            else:
                if callback:
                    callback("status", "Unknown document type, attempting text processing...")
                return self.text_agent.process_document(document_path)
        
        except Exception as e:
            if callback:
                callback("status", f"Error processing document: {str(e)}")
            return f"Error processing document: {str(e)}"
    
    def _generate_summary(self, document_results):
        """
        Generate a summary of all document findings
        
        Args:
            document_results (list): Results from document analysis
            
        Returns:
            str: Summary
        """
        # In a full implementation, this would use LLM to generate a coherent summary
        # For the prototype, we'll create a simple summary
        
        summary = "MEDICAL DOCUMENT ANALYSIS SUMMARY\n\n"
        
        for doc in document_results:
            filename = doc.get("filename", "Unknown document")
            doc_type = doc.get("type", "unknown")
            
            summary += f"Document: {filename} (Type: {doc_type})\n"
            
            # Extract key points (simplified for prototype)
            content = doc.get("content", "")
            lines = content.strip().split("\n")
            
            # Get first few lines for summary
            key_points = lines[:3] if len(lines) > 3 else lines
            for point in key_points:
                if point.strip():
                    summary += f"- {point.strip()}\n"
            
            summary += "\n"
        
        return summary
    
    def _generate_recommendations(self, document_results):
        """
        Generate recommendations based on document analysis
        
        Args:
            document_results (list): Results from document analysis
            
        Returns:
            str: Recommendations
        """
        # In a full implementation, this would use LLM to generate recommendations
        # For the prototype, we'll create placeholder recommendations
        
        recommendations = "RECOMMENDATIONS BASED ON DOCUMENT ANALYSIS\n\n"
        recommendations += "1. Please discuss these findings with your healthcare provider.\n"
        recommendations += "2. Regular follow-up is recommended for monitoring.\n"
        recommendations += "3. Consider additional testing as advised by your physician.\n\n"
        recommendations += "DISCLAIMER: These are automated suggestions and not a substitute for professional medical advice."
        
        return recommendations