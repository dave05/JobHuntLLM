"""Tests for the job fetcher module."""

import os
import sys
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the imports that might cause issues
sys.modules['requests'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['pandas'] = MagicMock()

from jobhuntgpt.job_fetcher import Job, fetch_from_csv, fetch_from_json, save_jobs_to_json, save_jobs_to_csv

# Sample job data for testing
SAMPLE_JOBS = [
    Job(
        title="Software Engineer",
        company="Example Corp",
        location="Remote",
        description="Looking for a software engineer with Python experience.",
        url="https://example.com/job1",
        date_posted="2023-07-01",
        source="test",
        salary="$100,000 - $120,000",
        job_type="Full-time"
    ),
    Job(
        title="Data Scientist",
        company="Test Inc",
        location="New York",
        description="Seeking a data scientist with machine learning expertise.",
        url="https://example.com/job2",
        date_posted="2023-07-02",
        source="test"
    )
]

def test_job_to_dict():
    """Test converting Job to dictionary."""
    job = SAMPLE_JOBS[0]
    job_dict = job.to_dict()

    assert job_dict["title"] == "Software Engineer"
    assert job_dict["company"] == "Example Corp"
    assert job_dict["location"] == "Remote"
    assert job_dict["description"] == "Looking for a software engineer with Python experience."
    assert job_dict["url"] == "https://example.com/job1"
    assert job_dict["date_posted"] == "2023-07-01"
    assert job_dict["source"] == "test"
    assert job_dict["salary"] == "$100,000 - $120,000"
    assert job_dict["job_type"] == "Full-time"

def test_job_from_dict():
    """Test creating Job from dictionary."""
    job_dict = {
        "title": "Software Engineer",
        "company": "Example Corp",
        "location": "Remote",
        "description": "Looking for a software engineer with Python experience.",
        "url": "https://example.com/job1",
        "date_posted": "2023-07-01",
        "source": "test",
        "salary": "$100,000 - $120,000",
        "job_type": "Full-time"
    }

    job = Job.from_dict(job_dict)

    assert job.title == "Software Engineer"
    assert job.company == "Example Corp"
    assert job.location == "Remote"
    assert job.description == "Looking for a software engineer with Python experience."
    assert job.url == "https://example.com/job1"
    assert job.date_posted == "2023-07-01"
    assert job.source == "test"
    assert job.salary == "$100,000 - $120,000"
    assert job.job_type == "Full-time"

def test_fetch_from_csv(tmp_path):
    """Test fetching jobs from CSV."""
    # Create a temporary CSV file with sample jobs
    csv_path = tmp_path / "sample_jobs.csv"
    with open(csv_path, 'w') as f:
        f.write("title,company,location,description,url,date_posted,salary,job_type\n")
        f.write("Software Engineer,Example Corp,Remote,Looking for a software engineer with Python experience.,https://example.com/job1,2023-07-01,$100000 - $120000,Full-time\n")
        f.write("Data Scientist,Test Inc,New York,Seeking a data scientist with machine learning expertise.,https://example.com/job2,2023-07-02,,\n")

    # Fetch jobs from CSV
    jobs = fetch_from_csv(str(csv_path))

    # Check results
    assert len(jobs) == 2
    assert jobs[0].title == "Software Engineer"
    assert jobs[0].company == "Example Corp"
    assert jobs[1].title == "Data Scientist"
    assert jobs[1].company == "Test Inc"

def test_fetch_from_json(tmp_path):
    """Test fetching jobs from JSON."""
    # Create a temporary JSON file with sample jobs
    json_path = tmp_path / "sample_jobs.json"
    with open(json_path, 'w') as f:
        json.dump([
            {
                "title": "Software Engineer",
                "company": "Example Corp",
                "location": "Remote",
                "description": "Looking for a software engineer with Python experience.",
                "url": "https://example.com/job1",
                "date_posted": "2023-07-01",
                "salary": "$100,000 - $120,000",
                "job_type": "Full-time"
            },
            {
                "title": "Data Scientist",
                "company": "Test Inc",
                "location": "New York",
                "description": "Seeking a data scientist with machine learning expertise.",
                "url": "https://example.com/job2",
                "date_posted": "2023-07-02"
            }
        ], f)

    # Fetch jobs from JSON
    jobs = fetch_from_json(str(json_path))

    # Check results
    assert len(jobs) == 2
    assert jobs[0].title == "Software Engineer"
    assert jobs[0].company == "Example Corp"
    assert jobs[1].title == "Data Scientist"
    assert jobs[1].company == "Test Inc"

def test_save_jobs_to_json(tmp_path):
    """Test saving jobs to JSON."""
    # Create a temporary JSON file
    json_path = tmp_path / "output_jobs.json"

    # Save jobs to JSON
    save_jobs_to_json(SAMPLE_JOBS, str(json_path))

    # Check if file exists
    assert os.path.exists(json_path)

    # Load jobs from JSON
    with open(json_path, 'r') as f:
        job_dicts = json.load(f)

    # Check results
    assert len(job_dicts) == 2
    assert job_dicts[0]["title"] == "Software Engineer"
    assert job_dicts[0]["company"] == "Example Corp"
    assert job_dicts[1]["title"] == "Data Scientist"
    assert job_dicts[1]["company"] == "Test Inc"

def test_save_jobs_to_csv(tmp_path):
    """Test saving jobs to CSV."""
    # Create a temporary CSV file
    csv_path = tmp_path / "output_jobs.csv"

    # Save jobs to CSV
    save_jobs_to_csv(SAMPLE_JOBS, str(csv_path))

    # Check if file exists
    assert os.path.exists(csv_path)

    # Load jobs from CSV
    jobs = fetch_from_csv(str(csv_path))

    # Check results
    assert len(jobs) == 2
    assert jobs[0].title == "Software Engineer"
    assert jobs[0].company == "Example Corp"
    assert jobs[1].title == "Data Scientist"
    assert jobs[1].company == "Test Inc"
