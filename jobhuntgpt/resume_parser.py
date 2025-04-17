"""Resume parser module for JobHuntGPT."""

import os
from typing import Dict, Any, List
import logging
from pathlib import Path

# Try to import pyresparser, but provide fallback if not available
try:
    from pyresparser import ResumeParser
    PYRESPARSER_AVAILABLE = True
except ImportError:
    PYRESPARSER_AVAILABLE = False
    logging.warning("pyresparser not available, falling back to basic parser")

import re
import PyPDF2
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

class ResumeParserError(Exception):
    """Exception raised for errors in the resume parser."""
    pass

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ResumeParserError(f"Failed to extract text from PDF: {e}")

def parse_with_pyresparser(resume_path: str) -> Dict[str, Any]:
    """
    Parse resume using pyresparser.
    
    Args:
        resume_path: Path to the resume file
        
    Returns:
        Dictionary containing parsed resume information
    """
    try:
        data = ResumeParser(resume_path).get_extracted_data()
        return {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "phone": data.get("mobile_number", ""),
            "skills": data.get("skills", []),
            "education": data.get("education", []),
            "experience": data.get("experience", []),
            "summary": data.get("summary", "")
        }
    except Exception as e:
        logger.error(f"Error parsing resume with pyresparser: {e}")
        raise ResumeParserError(f"Failed to parse resume with pyresparser: {e}")

def parse_with_llm(resume_text: str, llm_model_path: str) -> Dict[str, Any]:
    """
    Parse resume using LLaMA model.
    
    Args:
        resume_text: Text extracted from resume
        llm_model_path: Path to the LLaMA model
        
    Returns:
        Dictionary containing parsed resume information
    """
    try:
        # Initialize LLaMA model
        llm = LlamaCpp(
            model_path=llm_model_path,
            temperature=0.1,
            max_tokens=2048,
            n_ctx=4096,
            verbose=False
        )
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            Extract the following information from the resume text:
            1. Full Name
            2. Email Address
            3. Phone Number
            4. Skills (as a list)
            5. Work Experience (as a list of company, title, dates, and description)
            6. Education (as a list of institution, degree, dates)
            7. Summary or Objective
            
            Format your response as a JSON object with the following keys:
            name, email, phone, skills, experience, education, summary
            
            Resume Text:
            {resume_text}
            
            JSON Output:
            """
        )
        
        # Generate response
        response = llm(prompt.format(resume_text=resume_text))
        
        # Extract JSON from response
        import json
        import re
        
        # Find JSON-like content in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from LLM response")
                raise ResumeParserError("Failed to parse JSON from LLM response")
        else:
            logger.error("No JSON found in LLM response")
            raise ResumeParserError("No JSON found in LLM response")
            
    except Exception as e:
        logger.error(f"Error parsing resume with LLM: {e}")
        raise ResumeParserError(f"Failed to parse resume with LLM: {e}")

def parse_with_regex(resume_text: str) -> Dict[str, Any]:
    """
    Parse resume using regex patterns.
    
    Args:
        resume_text: Text extracted from resume
        
    Returns:
        Dictionary containing parsed resume information
    """
    # Basic patterns for extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
    
    # Extract email and phone
    email = re.search(email_pattern, resume_text)
    phone = re.search(phone_pattern, resume_text)
    
    # Extract name (assuming it's at the beginning of the resume)
    name_lines = resume_text.strip().split('\n')[:3]
    name = name_lines[0] if name_lines else ""
    
    # Extract skills (common keywords)
    skill_keywords = [
        "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "php",
        "html", "css", "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "git", "sql",
        "nosql", "mongodb", "postgresql", "mysql", "oracle", "data analysis",
        "machine learning", "ai", "artificial intelligence", "nlp", "natural language processing",
        "deep learning", "neural networks", "agile", "scrum", "kanban", "jira",
        "project management", "leadership", "communication", "teamwork", "problem solving"
    ]
    
    skills = []
    for skill in skill_keywords:
        if re.search(r'\b' + skill + r'\b', resume_text.lower()):
            skills.append(skill)
    
    return {
        "name": name.strip(),
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "skills": skills,
        "education": [],  # Would need more complex parsing
        "experience": [],  # Would need more complex parsing
        "summary": ""  # Would need more complex parsing
    }

def parse_resume(path: str, llm_model_path: str = None) -> Dict[str, Any]:
    """
    Parse a resume and extract relevant information.
    
    Args:
        path: Path to the resume file
        llm_model_path: Path to the LLaMA model (optional)
        
    Returns:
        Dictionary containing parsed resume information
    """
    # Check if file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Resume file not found: {path}")
    
    # Extract text from PDF if it's a PDF file
    if path.lower().endswith('.pdf'):
        resume_text = extract_text_from_pdf(path)
    else:
        # Assume it's a text file
        with open(path, 'r', encoding='utf-8') as file:
            resume_text = file.read()
    
    # Try parsing with pyresparser if available
    if PYRESPARSER_AVAILABLE:
        try:
            return parse_with_pyresparser(path)
        except ResumeParserError:
            logger.warning("pyresparser failed, falling back to alternative methods")
    
    # Try parsing with LLM if model path is provided
    if llm_model_path and os.path.exists(llm_model_path):
        try:
            return parse_with_llm(resume_text, llm_model_path)
        except ResumeParserError:
            logger.warning("LLM parsing failed, falling back to regex parser")
    
    # Fall back to regex parser
    return parse_with_regex(resume_text)

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
        result = parse_resume(resume_path)
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Please provide a path to a resume file")
