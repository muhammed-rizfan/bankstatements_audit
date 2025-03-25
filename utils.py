import os
import subprocess
import tempfile
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdftotext (poppler) command line tool"""
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Use pdftotext (from poppler) to extract text
        # This tool often works better with secured PDFs
        cmd = ['pdftotext', '-layout', pdf_path, temp_path]
        subprocess.run(cmd, check=True)
        
        # Read the extracted text
        with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return text
    except subprocess.CalledProcessError:
        print("Error: pdftotext command failed. Make sure poppler-utils is installed.")
        print("  - On macOS: brew install poppler")
        print("  - On Ubuntu: sudo apt-get install poppler-utils")
        return None
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None 