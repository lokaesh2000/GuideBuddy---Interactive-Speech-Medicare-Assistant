"""
Structured Data Agent
Agent for processing structured medical data like lab results
"""

import os
import csv
import pandas as pd
from services.llm_service import LLMService

class StructuredAgent:
    """Agent for processing structured data documents"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def process_document(self, document_path):
        """
        Process a structured data document
        
        Args:
            document_path (str): Path to the document
            
        Returns:
            str: Analysis results
        """
        # Extract data from the document
        data = self._extract_data(document_path)
        
        # If extraction failed, return the error
        if isinstance(data, str):
            return data
        
        # Analyze the data
        analysis = self._analyze_data(data, os.path.basename(document_path))
        
        return analysis
    
    def _extract_data(self, document_path):
        """
        Extract data from a structured document
        
        Args:
            document_path (str): Path to the document
            
        Returns:
            pandas.DataFrame or str: Extracted data or error message
        """
        # Get file extension
        _, ext = os.path.splitext(document_path)
        ext = ext.lower()
        
        try:
            # CSV files
            if ext == '.csv':
                return pd.read_csv(document_path)
            
            # Excel files
            elif ext in ['.xlsx', '.xls']:
                return pd.read_excel(document_path)
            
            # Unsupported format
            else:
                return "Unsupported structured data format."
        
        except Exception as e:
            return f"Error extracting data: {str(e)}"
    
    def _analyze_data(self, data, filename):
        """
        Analyze structured medical data
        
        Args:
            data (pandas.DataFrame): Structured data
            filename (str): Name of the original file
            
        Returns:
            str: Analysis results
        """
        # Start the analysis report
        analysis = "STRUCTURED DATA ANALYSIS\n\n"
        analysis += f"File: {filename}\n\n"
        
        # If data is an error message, return it
        if isinstance(data, str):
            analysis += f"Error: {data}\n"
            return analysis
        
        # Basic data overview
        analysis += "DATA OVERVIEW:\n"
        analysis += f"- Rows: {data.shape[0]}\n"
        analysis += f"- Columns: {data.shape[1]}\n"
        analysis += f"- Column names: {', '.join(data.columns.tolist())}\n\n"
        
        # Try to identify if this is lab data
        is_lab_data = self._check_if_lab_data(data)
        
        if is_lab_data:
            analysis += self._analyze_lab_data(data)
        else:
            analysis += self._analyze_generic_data(data)
        
        # Add disclaimer
        analysis += "\nNOTE: This is a simulated analysis for prototype purposes. In the final implementation, "
        analysis += "this would use the Gemini LLM for comprehensive analysis of structured medical data."
        
        return analysis
    
    def _check_if_lab_data(self, data):
        """
        Check if the data appears to be lab results
        
        Args:
            data (pandas.DataFrame): Data to check
            
        Returns:
            bool: True if it appears to be lab data
        """
        # Look for common lab data column names
        lab_related_columns = [
            'test', 'lab', 'result', 'value', 'reference', 'range', 'unit',
            'normal', 'high', 'low', 'wbc', 'rbc', 'hgb', 'plt', 'glucose'
        ]
        
        columns_lower = [col.lower() for col in data.columns]
        
        # Check if any common lab column names are present
        for term in lab_related_columns:
            for col in columns_lower:
                if term in col:
                    return True
        
        return False
    
    def _analyze_lab_data(self, data):
        """
        Analyze laboratory test data
        
        Args:
            data (pandas.DataFrame): Lab data
            
        Returns:
            str: Analysis
        """
        analysis = "LABORATORY DATA ANALYSIS:\n"
        
        # Try to identify test name, result, and reference range columns
        test_col = None
        result_col = None
        ref_col = None
        
        # Look for column names that match patterns
        for col in data.columns:
            col_lower = col.lower()
            if 'test' in col_lower or 'name' in col_lower:
                test_col = col
            elif 'result' in col_lower or 'value' in col_lower:
                result_col = col
            elif 'reference' in col_lower or 'range' in col_lower or 'normal' in col_lower:
                ref_col = col
        
        # If we found test and result columns, analyze abnormal results
        if test_col and result_col:
            analysis += "Potentially abnormal results:\n"
            
            abnormal_found = False
            
            # Iterate through rows to find abnormal results
            for _, row in data.iterrows():
                test_name = row[test_col]
                result = row[result_col]
                
                # Skip rows with missing data
                if pd.isna(test_name) or pd.isna(result):
                    continue
                
                # Convert result to string for analysis
                result_str = str(result)
                
                # Check if result includes H or L flags for high/low
                if 'H' in result_str or 'h' in result_str:
                    abnormal_found = True
                    ref_range = row[ref_col] if ref_col and not pd.isna(row[ref_col]) else "N/A"
                    analysis += f"- {test_name}: {result} (HIGH) - Reference: {ref_range}\n"
                elif 'L' in result_str or 'l' in result_str:
                    abnormal_found = True
                    ref_range = row[ref_col] if ref_col and not pd.isna(row[ref_col]) else "N/A"
                    analysis += f"- {test_name}: {result} (LOW) - Reference: {ref_range}\n"
            
            if not abnormal_found:
                analysis += "- No clearly abnormal results identified in the data\n"
        
        else:
            # If we couldn't identify the right columns, show statistical summary
            analysis += "Statistical summary of numerical columns:\n"
            
            numeric_cols = data.select_dtypes(include=['number']).columns
            
            for col in numeric_cols:
                if data[col].count() > 0:  # Only include columns with data
                    analysis += f"- {col}:\n"
                    analysis += f"  Average: {data[col].mean():.2f}\n"
                    analysis += f"  Min: {data[col].min():.2f}\n"
                    analysis += f"  Max: {data[col].max():.2f}\n"
        
        return analysis
    
    def _analyze_generic_data(self, data):
        """
        Provide a generic analysis of structured data
        
        Args:
            data (pandas.DataFrame): Data to analyze
            
        Returns:
            str: Analysis
        """
        analysis = "GENERAL DATA ANALYSIS:\n"
        
        # Data completeness
        missing_values = data.isnull().sum()
        columns_with_missing = missing_values[missing_values > 0]
        
        if not columns_with_missing.empty:
            analysis += "Columns with missing values:\n"
            for col, count in columns_with_missing.items():
                analysis += f"- {col}: {count} missing values ({count/len(data)*100:.1f}%)\n"
        else:
            analysis += "No missing values found in the data.\n"
        
        # Sample of first few rows
        analysis += "\nSample data (first 3 rows):\n"
        
        # Convert the sample data to a readable format
        sample = data.head(3)
        rows = []
        
        for _, row in sample.iterrows():
            row_str = " | ".join([f"{col}: {row[col]}" for col in sample.columns])
            rows.append(f"- {row_str}")
        
        analysis += "\n".join(rows)
        
        return analysis