"""Tests for the matcher module."""

import os
import sys
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jobhuntgpt.matcher import (
    create_resume_summary, create_job_summary, compute_similarity,
    get_matching_skills, get_missing_skills
)
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

def test_create_resume_summary():
    """Test creating resume summary."""
    summary = create_resume_summary(SAMPLE_RESUME)

    # Check if summary contains important information
    assert "John Doe" in summary
    assert "Python" in summary
    assert "JavaScript" in summary
    assert "Software Engineer" in summary
    assert "ABC Tech" in summary
    assert "University of Example" in summary

def test_create_job_summary():
    """Test creating job summary."""
    summary = create_job_summary(SAMPLE_JOB)

    # Check if summary contains important information
    assert "Senior Software Engineer" in summary
    assert "Example Corp" in summary
    assert "Remote" in summary
    assert "Python" in summary
    assert "React" in summary
    assert "Node.js" in summary
    assert "$120,000 - $150,000" in summary
    assert "Full-time" in summary

def test_compute_similarity():
    """Test computing similarity between embeddings."""
    # Create mock embeddings
    resume_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    job_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])  # Identical, should be 1.0

    # Compute similarity
    similarity = compute_similarity(resume_embedding, job_embedding)

    # Check result
    assert similarity == 1.0

    # Test with different embeddings
    job_embedding2 = np.array([0.5, 0.4, 0.3, 0.2, 0.1])  # Reversed, should be less than 1.0
    similarity2 = compute_similarity(resume_embedding, job_embedding2)

    # Check result
    assert similarity2 < 1.0

def test_get_matching_skills():
    """Test getting matching skills."""
    # Get matching skills
    matching_skills = get_matching_skills(SAMPLE_RESUME, SAMPLE_JOB)

    # Check results
    assert "Python" in matching_skills
    assert "React" in matching_skills
    assert "Node.js" in matching_skills
    assert "Machine Learning" in matching_skills

    # SQL is in the resume but not mentioned in the job description
    assert "SQL" not in matching_skills

def test_get_missing_skills():
    """Test getting missing skills."""
    # Define common skills to check for
    common_skills = ["Python", "JavaScript", "React", "Node.js", "SQL", "Machine Learning", "Docker", "Kubernetes"]

    # Get missing skills
    missing_skills = get_missing_skills(SAMPLE_RESUME, SAMPLE_JOB, common_skills)

    # Check results
    # Docker and Kubernetes are in the common skills list and mentioned in the job description,
    # but not in the resume, so they should be identified as missing
    assert "Docker" not in missing_skills  # Not mentioned in job description
    assert "Kubernetes" not in missing_skills  # Not mentioned in job description

    # Create a job with Docker and Kubernetes in the description
    job_with_docker = Job(
        title="DevOps Engineer",
        company="Example Corp",
        location="Remote",
        description="Looking for a DevOps engineer with experience in Docker and Kubernetes.",
        url="https://example.com/job2",
        date_posted="2023-07-01",
        source="test"
    )

    # Get missing skills for the new job
    missing_skills2 = get_missing_skills(SAMPLE_RESUME, job_with_docker, common_skills)

    # Check results
    assert "Docker" in missing_skills2
    assert "Kubernetes" in missing_skills2
