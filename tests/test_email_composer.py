"""Tests for the email composer module."""

import pytest
from jobhuntgpt.email_composer import compose_cover_letter, compose_followup, compose_thank_you
from jobhuntgpt.job_fetcher import Job

# Sample resume data for testing
SAMPLE_RESUME = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "(123) 456-7890",
    "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Machine Learning"],
    "experience": [
        {
            "company": "ABC Tech",
            "title": "Software Engineer",
            "dates": "2020-2023",
            "description": "Developed web applications using React and Node.js"
        },
        {
            "company": "XYZ Analytics",
            "title": "Data Scientist",
            "dates": "2018-2020",
            "description": "Analyzed large datasets using Python and SQL"
        }
    ],
    "education": [
        {
            "institution": "University of Example",
            "degree": "Master of Science in Computer Science",
            "dates": "2016-2018"
        }
    ],
    "summary": "Experienced software engineer with expertise in Python, JavaScript, and machine learning."
}

# Sample job data for testing
SAMPLE_JOB = Job(
    title="Senior Software Engineer",
    company="Example Corp",
    location="Remote",
    description="Looking for a senior software engineer with experience in Python, React, and Node.js. Knowledge of machine learning is a plus.",
    url="https://example.com/job1",
    date_posted="2023-07-01",
    source="test",
    salary="$120,000 - $150,000",
    job_type="Full-time"
)

def test_compose_cover_letter():
    """Test composing a cover letter."""
    # Compose cover letter
    cover_letter = compose_cover_letter(SAMPLE_JOB, SAMPLE_RESUME)
    
    # Check if cover letter contains important information
    assert "John Doe" in cover_letter
    assert "Senior Software Engineer" in cover_letter
    assert "Example Corp" in cover_letter
    assert "Python" in cover_letter or "React" in cover_letter or "Node.js" in cover_letter
    
    # Check structure
    assert "Dear" in cover_letter
    assert "Sincerely" in cover_letter

def test_compose_followup():
    """Test composing a follow-up email."""
    # Create a sample previous email
    previous_email = """
    July 15, 2023

    Dear Hiring Manager,

    I am writing to express my interest in the Senior Software Engineer position at Example Corp.

    Sincerely,
    John Doe
    john.doe@example.com
    (123) 456-7890
    """
    
    # Compose follow-up email
    followup_email = compose_followup(SAMPLE_JOB, previous_email, 7)
    
    # Check if follow-up email contains important information
    assert "John Doe" in followup_email
    assert "Senior Software Engineer" in followup_email
    assert "Example Corp" in followup_email
    assert "follow" in followup_email.lower() or "application" in followup_email.lower()
    
    # Check structure
    assert "Dear" in followup_email
    assert "Sincerely" in followup_email

def test_compose_thank_you():
    """Test composing a thank you email."""
    # Compose thank you email
    thank_you_email = compose_thank_you(SAMPLE_JOB, "Jane Smith", "We discussed my experience with Python and React.")
    
    # Check if thank you email contains important information
    assert "Jane Smith" in thank_you_email
    assert "Senior Software Engineer" in thank_you_email
    assert "Example Corp" in thank_you_email
    assert "thank" in thank_you_email.lower()
    assert "interview" in thank_you_email.lower()
    assert "Python" in thank_you_email or "React" in thank_you_email
    
    # Check structure
    assert "Dear" in thank_you_email
    assert "Sincerely" in thank_you_email
