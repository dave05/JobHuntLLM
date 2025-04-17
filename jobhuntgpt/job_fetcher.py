"""Job fetcher module for JobHuntGPT."""

import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class Job:
    """Job posting data class."""
    
    title: str
    company: str
    location: str
    description: str
    url: str
    date_posted: str
    source: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Job to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "date_posted": self.date_posted,
            "source": self.source,
            "salary": self.salary,
            "job_type": self.job_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary."""
        return cls(
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            date_posted=data.get("date_posted", ""),
            source=data.get("source", ""),
            salary=data.get("salary"),
            job_type=data.get("job_type")
        )

class JobFetcherError(Exception):
    """Exception raised for errors in the job fetcher."""
    pass

def fetch_from_csv(file_path: str) -> List[Job]:
    """
    Fetch job listings from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of Job objects
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    try:
        jobs = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Check for required fields
                if not all(key in row for key in ["title", "company", "location", "description", "url"]):
                    logger.warning(f"Skipping row with missing required fields: {row}")
                    continue
                
                # Create Job object
                job = Job(
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    description=row["description"],
                    url=row["url"],
                    date_posted=row.get("date_posted", datetime.now().strftime("%Y-%m-%d")),
                    source="csv",
                    salary=row.get("salary"),
                    job_type=row.get("job_type")
                )
                jobs.append(job)
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs from CSV: {e}")
        raise JobFetcherError(f"Failed to fetch jobs from CSV: {e}")

def fetch_from_json(file_path: str) -> List[Job]:
    """
    Fetch job listings from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of Job objects
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        jobs = []
        for item in data:
            # Check for required fields
            if not all(key in item for key in ["title", "company", "location", "description", "url"]):
                logger.warning(f"Skipping item with missing required fields: {item}")
                continue
            
            # Create Job object
            job = Job(
                title=item["title"],
                company=item["company"],
                location=item["location"],
                description=item["description"],
                url=item["url"],
                date_posted=item.get("date_posted", datetime.now().strftime("%Y-%m-%d")),
                source="json",
                salary=item.get("salary"),
                job_type=item.get("job_type")
            )
            jobs.append(job)
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs from JSON: {e}")
        raise JobFetcherError(f"Failed to fetch jobs from JSON: {e}")

def fetch_from_linkedin(query: str, location: str = "remote", limit: int = 10, api_key: Optional[str] = None) -> List[Job]:
    """
    Fetch job listings from LinkedIn.
    
    Args:
        query: Job search query
        location: Job location
        limit: Maximum number of jobs to fetch
        api_key: LinkedIn API key (optional)
        
    Returns:
        List of Job objects
    """
    # This is a mock implementation since we don't have actual LinkedIn API access
    # In a real implementation, you would use the LinkedIn API with the provided API key
    
    logger.warning("LinkedIn API not implemented. Using web scraping as fallback.")
    
    try:
        # Format the query for the URL
        formatted_query = query.replace(" ", "%20")
        formatted_location = location.replace(" ", "%20")
        
        # LinkedIn job search URL
        url = f"https://www.linkedin.com/jobs/search/?keywords={formatted_query}&location={formatted_location}"
        
        # Send request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract job listings
        job_cards = soup.find_all("div", class_="base-card")
        
        jobs = []
        for card in job_cards[:limit]:
            try:
                # Extract job details
                title_elem = card.find("h3", class_="base-search-card__title")
                company_elem = card.find("h4", class_="base-search-card__subtitle")
                location_elem = card.find("span", class_="job-search-card__location")
                link_elem = card.find("a", class_="base-card__full-link")
                
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                job_location = location_elem.text.strip() if location_elem else location
                url = link_elem["href"] if link_elem else ""
                
                # Get job description (would require another request to the job page)
                description = f"Job posting for {title} at {company}. Visit the URL for more details."
                
                # Create Job object
                job = Job(
                    title=title,
                    company=company,
                    location=job_location,
                    description=description,
                    url=url,
                    date_posted=datetime.now().strftime("%Y-%m-%d"),
                    source="linkedin"
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing job card: {e}")
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs from LinkedIn: {e}")
        raise JobFetcherError(f"Failed to fetch jobs from LinkedIn: {e}")

def fetch_from_indeed(query: str, location: str = "remote", limit: int = 10, api_key: Optional[str] = None) -> List[Job]:
    """
    Fetch job listings from Indeed.
    
    Args:
        query: Job search query
        location: Job location
        limit: Maximum number of jobs to fetch
        api_key: Indeed API key (optional)
        
    Returns:
        List of Job objects
    """
    # This is a mock implementation since we don't have actual Indeed API access
    # In a real implementation, you would use the Indeed API with the provided API key
    
    logger.warning("Indeed API not implemented. Using web scraping as fallback.")
    
    try:
        # Format the query for the URL
        formatted_query = query.replace(" ", "+")
        formatted_location = location.replace(" ", "+")
        
        # Indeed job search URL
        url = f"https://www.indeed.com/jobs?q={formatted_query}&l={formatted_location}"
        
        # Send request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract job listings
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        
        jobs = []
        for card in job_cards[:limit]:
            try:
                # Extract job details
                title_elem = card.find("h2", class_="jobTitle")
                company_elem = card.find("span", class_="companyName")
                location_elem = card.find("div", class_="companyLocation")
                
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                job_location = location_elem.text.strip() if location_elem else location
                
                # Get job URL
                url_elem = card.find("a", class_="jcs-JobTitle")
                url = "https://www.indeed.com" + url_elem["href"] if url_elem and "href" in url_elem.attrs else ""
                
                # Get job description (would require another request to the job page)
                description = f"Job posting for {title} at {company}. Visit the URL for more details."
                
                # Create Job object
                job = Job(
                    title=title,
                    company=company,
                    location=job_location,
                    description=description,
                    url=url,
                    date_posted=datetime.now().strftime("%Y-%m-%d"),
                    source="indeed"
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing job card: {e}")
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs from Indeed: {e}")
        raise JobFetcherError(f"Failed to fetch jobs from Indeed: {e}")

def fetch_jobs(source: str, query: str = "software engineer", location: str = "remote", 
               limit: int = 10, api_key: Optional[str] = None) -> List[Job]:
    """
    Fetch job listings from the specified source.
    
    Args:
        source: Source to fetch jobs from (linkedin, indeed, csv, json)
        query: Job search query (for API sources)
        location: Job location (for API sources)
        limit: Maximum number of jobs to fetch
        api_key: API key for the source (if required)
        
    Returns:
        List of Job objects
    """
    source = source.lower()
    
    if source == "linkedin":
        return fetch_from_linkedin(query, location, limit, api_key)
    elif source == "indeed":
        return fetch_from_indeed(query, location, limit, api_key)
    elif source == "csv":
        return fetch_from_csv(query)  # In this case, query is the file path
    elif source == "json":
        return fetch_from_json(query)  # In this case, query is the file path
    else:
        raise ValueError(f"Unsupported source: {source}")

def save_jobs_to_csv(jobs: List[Job], file_path: str) -> None:
    """
    Save job listings to a CSV file.
    
    Args:
        jobs: List of Job objects
        file_path: Path to save the CSV file
    """
    try:
        # Convert jobs to dictionaries
        job_dicts = [job.to_dict() for job in jobs]
        
        # Create DataFrame
        df = pd.DataFrame(job_dicts)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        
        logger.info(f"Saved {len(jobs)} jobs to {file_path}")
    except Exception as e:
        logger.error(f"Error saving jobs to CSV: {e}")
        raise JobFetcherError(f"Failed to save jobs to CSV: {e}")

def save_jobs_to_json(jobs: List[Job], file_path: str) -> None:
    """
    Save job listings to a JSON file.
    
    Args:
        jobs: List of Job objects
        file_path: Path to save the JSON file
    """
    try:
        # Convert jobs to dictionaries
        job_dicts = [job.to_dict() for job in jobs]
        
        # Save to JSON
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(job_dicts, file, indent=2)
        
        logger.info(f"Saved {len(jobs)} jobs to {file_path}")
    except Exception as e:
        logger.error(f"Error saving jobs to JSON: {e}")
        raise JobFetcherError(f"Failed to save jobs to JSON: {e}")

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python job_fetcher.py <source> <query_or_file_path> [location] [limit]")
        sys.exit(1)
    
    source = sys.argv[1]
    query_or_file = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else "remote"
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    jobs = fetch_jobs(source, query_or_file, location, limit)
    
    print(f"Found {len(jobs)} jobs:")
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title} at {job.company} ({job.location})")
