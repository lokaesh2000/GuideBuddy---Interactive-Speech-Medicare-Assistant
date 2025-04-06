"""
Document Controller
Handles document upload, processing, and analysis
"""

import os
import json
import shutil
import threading
import datetime
from config.settings import get_user_dir
from agents.coordinator import CoordinatorAgent

class DocumentController:
    """Controller for document operations"""
    
    def __init__(self, user_data):
        self.user_data = user_data
        self.user_dir = get_user_dir(user_data["username"], user_data["user_type"])
        self.documents_dir = os.path.join(self.user_dir, "documents")
        self.reports_dir = os.path.join(self.user_dir, "reports")
        
        # Create directories if they don't exist
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize coordinator agent
        self.coordinator = CoordinatorAgent()
    
    def upload_document(self, file_path, callback=None):
        """
        Upload and store a document
        
        Args:
            file_path (str): Path to the file to upload
            callback (function): Optional callback for progress updates
            
        Returns:
            str: Path to the stored document
        """
        if not os.path.exists(file_path):
            if callback:
                callback("status", "File not found")
            return None
        
        try:
            # Get the filename
            filename = os.path.basename(file_path)
            
            # Add timestamp to prevent overwriting
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            timestamped_filename = f"{name}_{timestamp}{ext}"
            
            # Destination path
            dest_path = os.path.join(self.documents_dir, timestamped_filename)
            
            # Copy the file
            shutil.copy2(file_path, dest_path)
            
            if callback:
                callback("status", f"Uploaded {filename}")
                callback("document_added", dest_path)
            
            return dest_path
        
        except Exception as e:
            if callback:
                callback("status", f"Upload error: {str(e)}")
            return None
    
    def get_documents(self):
        """
        Get list of user's documents
        
        Returns:
            list: List of document paths
        """
        if not os.path.exists(self.documents_dir):
            return []
        
        documents = []
        for filename in os.listdir(self.documents_dir):
            file_path = os.path.join(self.documents_dir, filename)
            if os.path.isfile(file_path):
                documents.append(file_path)
        
        return sorted(documents, key=os.path.getmtime, reverse=True)
    
    def get_reports(self):
        """
        Get list of analysis reports
        
        Returns:
            list: List of report paths
        """
        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)
        
        if not os.path.exists(self.reports_dir):
            return []
        
        reports = []
        for filename in os.listdir(self.reports_dir):
            file_path = os.path.join(self.reports_dir, filename)
            if os.path.isfile(file_path):
                reports.append(file_path)
        
        return sorted(reports, key=os.path.getmtime, reverse=True)
    
    def delete_document(self, document_path):
        """
        Delete a document
        
        Args:
            document_path (str): Path to the document to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if os.path.exists(document_path) and document_path.startswith(self.documents_dir):
            try:
                os.remove(document_path)
                return True
            except Exception:
                return False
        return False
    
    def process_documents(self, document_paths, callback=None):
        """
        Process documents with multi-agent system
        
        Args:
            document_paths (list): List of paths to documents
            callback (function): Optional callback for progress updates
            
        Returns:
            str: Path to the generated report
        """
        # Run in a background thread to prevent UI blocking
        thread = threading.Thread(
            target=self._process_documents_thread,
            args=(document_paths, callback),
            daemon=True
        )
        thread.start()
    
    def _process_documents_thread(self, document_paths, callback):
        """Background thread to process documents"""
        if callback:
            callback("status", "Starting document analysis...")
        
        try:
            # Ensure reports directory exists
            os.makedirs(self.reports_dir, exist_ok=True)
            
            # Analyze documents using coordinator agent
            results = self.coordinator.analyze_documents(document_paths, callback)
            
            # Generate report filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{self.user_data['username']}_Report_{timestamp}.pdf"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # Generate PDF report
            self._generate_report(results, report_path)
            
            if callback:
                callback("status", "Analysis complete")
                callback("report_generated", report_path)
            
            return report_path
            
        except Exception as e:
            if callback:
                callback("status", f"Analysis error: {str(e)}")
            return None
    
    def _generate_report(self, analysis_results, output_path):
        """
        Generate a PDF report from analysis results
        
        Args:
            analysis_results (dict): Results from document analysis
            output_path (str): Path to save the PDF report
        """
        # This would use a PDF generation library like reportlab
        # For the prototype, we'll create a simple text file instead
        
        # Save as JSON for now (would be PDF in final version)
        with open(output_path.replace('.pdf', '.json'), 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        # Create a simple text version as well
        with open(output_path.replace('.pdf', '.txt'), 'w') as f:
            f.write(f"Medical Document Analysis Report\n")
            f.write(f"Patient: {self.user_data['name']}\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add summary if available
            if 'summary' in analysis_results:
                f.write("SUMMARY\n")
                f.write("=======\n")
                f.write(analysis_results['summary'])
                f.write("\n\n")
            
            # Add document-specific analysis
            if 'documents' in analysis_results:
                f.write("DOCUMENT ANALYSIS\n")
                f.write("=================\n")
                
                for doc in analysis_results['documents']:
                    f.write(f"Document: {doc.get('filename', 'Unknown')}\n")
                    f.write(f"Type: {doc.get('type', 'Unknown')}\n")
                    
                    if 'content' in doc:
                        f.write("Content:\n")
                        f.write(doc['content'])
                    
                    f.write("\n\n")
            
            # Add recommendations if available
            if 'recommendations' in analysis_results:
                f.write("RECOMMENDATIONS\n")
                f.write("===============\n")
                f.write(analysis_results['recommendations'])
        
        return output_path.replace('.pdf', '.txt')