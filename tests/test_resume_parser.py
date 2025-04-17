"""Tests for the resume parser module."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the imports that might cause issues
sys.modules['PyPDF2'] = MagicMock()
sys.modules['langchain.llms'] = MagicMock()
sys.modules['langchain.prompts'] = MagicMock()

from jobhuntgpt.resume_parser import parse_resume, extract_text_from_pdf, parse_with_regex

# Sample resume text for testing
SAMPLE_RESUME_TEXT = """
John Doe
john.doe@example.com
(123) 456-7890

Summary:
Experienced software engineer with expertise in Python, JavaScript, and machine learning.

Skills:
Python, JavaScript, React, Node.js, SQL, Machine Learning, TensorFlow, Docker, Kubernetes

Experience:
Software Engineer, ABC Tech (2020-2023)
- Developed web applications using React and Node.js
- Implemented machine learning models for data analysis
- Managed Docker containers and Kubernetes clusters

Data Scientist, XYZ Analytics (2018-2020)
- Analyzed large datasets using Python and SQL
- Built predictive models using TensorFlow and scikit-learn
- Created data visualizations for stakeholder presentations

Education:
Master of Science in Computer Science, University of Example (2016-2018)
Bachelor of Science in Mathematics, Example College (2012-2016)
"""

def test_parse_with_regex():
    """Test parsing resume with regex."""
    result = parse_with_regex(SAMPLE_RESUME_TEXT)

    # Check basic fields
    assert "John Doe" in result["name"]
    assert "john.doe@example.com" == result["email"]
    # The phone number format might vary slightly, so we'll check for the digits
    assert "456-7890" in result["phone"]

    # Check skills
    assert "python" in [skill.lower() for skill in result["skills"]]
    assert "javascript" in [skill.lower() for skill in result["skills"]]
    assert "react" in [skill.lower() for skill in result["skills"]]

@patch('jobhuntgpt.resume_parser.extract_text_from_pdf')
def test_extract_text_from_pdf(mock_extract_text, tmp_path):
    """Test extracting text from PDF (mock test)."""
    # This is a mock test since we can't create a real PDF in the test
    # In a real test, you would create a sample PDF file and test with it

    # Configure the mock to return the sample resume text
    mock_extract_text.return_value = SAMPLE_RESUME_TEXT

    # Create a temporary file
    pdf_path = tmp_path / "sample_resume.pdf"
    with open(pdf_path, 'w') as f:
        f.write("Mock PDF content")

    # Call parse_resume
    result = parse_resume(str(pdf_path))

    # Check basic fields
    assert "John Doe" in result["name"]
    assert "john.doe@example.com" == result["email"]
    assert "(123) 456-7890" == result["phone"]

    # Verify the mock was called
    mock_extract_text.assert_called_once_with(str(pdf_path))

@patch('jobhuntgpt.resume_parser.PYRESPARSER_AVAILABLE', False)
def test_parse_resume_with_text_file(tmp_path):
    """Test parsing resume from a text file."""
    # Create a temporary text file with sample resume
    resume_path = tmp_path / "sample_resume.txt"
    with open(resume_path, 'w') as f:
        f.write(SAMPLE_RESUME_TEXT)

    # Parse the resume
    result = parse_resume(str(resume_path))

    # Check basic fields
    assert "John Doe" in result["name"]
    assert "john.doe@example.com" == result["email"]
    assert "(123) 456-7890" == result["phone"]

    # Check skills
    assert len(result["skills"]) > 0
