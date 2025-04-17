"""Job matcher module for JobHuntGPT."""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from jobhuntgpt.job_fetcher import Job

logger = logging.getLogger(__name__)

class MatcherError(Exception):
    """Exception raised for errors in the matcher."""
    pass

def create_resume_summary(resume: Dict[str, Any]) -> str:
    """
    Create a summary of the resume for embedding.
    
    Args:
        resume: Dictionary containing parsed resume information
        
    Returns:
        Summary string
    """
    # Extract relevant information from the resume
    name = resume.get("name", "")
    skills = resume.get("skills", [])
    experience = resume.get("experience", [])
    education = resume.get("education", [])
    summary = resume.get("summary", "")
    
    # Format skills
    skills_str = ", ".join(skills)
    
    # Format experience
    experience_str = ""
    if isinstance(experience, list):
        for exp in experience:
            if isinstance(exp, dict):
                company = exp.get("company", "")
                title = exp.get("title", "")
                description = exp.get("description", "")
                experience_str += f"{title} at {company}: {description}. "
            elif isinstance(exp, str):
                experience_str += exp + ". "
    
    # Format education
    education_str = ""
    if isinstance(education, list):
        for edu in education:
            if isinstance(edu, dict):
                institution = edu.get("institution", "")
                degree = edu.get("degree", "")
                education_str += f"{degree} from {institution}. "
            elif isinstance(edu, str):
                education_str += edu + ". "
    
    # Combine all information
    resume_summary = f"""
    {name} Resume Summary:
    
    Skills: {skills_str}
    
    Experience: {experience_str}
    
    Education: {education_str}
    
    Summary: {summary}
    """
    
    return resume_summary.strip()

def create_job_summary(job: Job) -> str:
    """
    Create a summary of the job for embedding.
    
    Args:
        job: Job object
        
    Returns:
        Summary string
    """
    # Combine relevant job information
    job_summary = f"""
    Job Title: {job.title}
    
    Company: {job.company}
    
    Location: {job.location}
    
    Description: {job.description}
    
    Job Type: {job.job_type if job.job_type else "Not specified"}
    
    Salary: {job.salary if job.salary else "Not specified"}
    """
    
    return job_summary.strip()

def compute_similarity(resume_embedding: np.ndarray, job_embedding: np.ndarray) -> float:
    """
    Compute cosine similarity between resume and job embeddings.
    
    Args:
        resume_embedding: Resume embedding vector
        job_embedding: Job embedding vector
        
    Returns:
        Similarity score (0-1)
    """
    # Reshape embeddings for sklearn's cosine_similarity
    resume_embedding = resume_embedding.reshape(1, -1)
    job_embedding = job_embedding.reshape(1, -1)
    
    # Compute cosine similarity
    similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
    
    return float(similarity)

def rank_jobs(resume: Dict[str, Any], jobs: List[Job], top_k: int = 10, 
              model_name: str = "all-MiniLM-L6-v2") -> List[Tuple[Job, float]]:
    """
    Rank jobs based on similarity to resume.
    
    Args:
        resume: Dictionary containing parsed resume information
        jobs: List of Job objects
        top_k: Number of top jobs to return
        model_name: Name of the sentence transformer model to use
        
    Returns:
        List of tuples (Job, similarity_score) sorted by similarity score
    """
    try:
        # Load sentence transformer model
        model = SentenceTransformer(model_name)
        
        # Create resume summary
        resume_summary = create_resume_summary(resume)
        
        # Encode resume summary
        resume_embedding = model.encode(resume_summary)
        
        # Process each job
        job_similarities = []
        for job in jobs:
            # Create job summary
            job_summary = create_job_summary(job)
            
            # Encode job summary
            job_embedding = model.encode(job_summary)
            
            # Compute similarity
            similarity = compute_similarity(resume_embedding, job_embedding)
            
            # Add to list
            job_similarities.append((job, similarity))
        
        # Sort by similarity score (descending)
        job_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k jobs
        return job_similarities[:top_k]
    
    except Exception as e:
        logger.error(f"Error ranking jobs: {e}")
        raise MatcherError(f"Failed to rank jobs: {e}")

def get_matching_skills(resume: Dict[str, Any], job: Job) -> List[str]:
    """
    Get skills from the resume that match the job description.
    
    Args:
        resume: Dictionary containing parsed resume information
        job: Job object
        
    Returns:
        List of matching skills
    """
    # Extract skills from resume
    resume_skills = resume.get("skills", [])
    
    # Convert to lowercase for case-insensitive matching
    resume_skills_lower = [skill.lower() for skill in resume_skills]
    
    # Extract skills from job description
    job_description_lower = job.description.lower()
    
    # Find matching skills
    matching_skills = []
    for skill in resume_skills:
        if skill.lower() in job_description_lower:
            matching_skills.append(skill)
    
    return matching_skills

def get_missing_skills(resume: Dict[str, Any], job: Job, common_skills: List[str]) -> List[str]:
    """
    Get skills mentioned in the job description that are not in the resume.
    
    Args:
        resume: Dictionary containing parsed resume information
        job: Job object
        common_skills: List of common skills to check for
        
    Returns:
        List of missing skills
    """
    # Extract skills from resume
    resume_skills = resume.get("skills", [])
    
    # Convert to lowercase for case-insensitive matching
    resume_skills_lower = [skill.lower() for skill in resume_skills]
    
    # Extract skills from job description
    job_description_lower = job.description.lower()
    
    # Find missing skills
    missing_skills = []
    for skill in common_skills:
        if skill.lower() in job_description_lower and skill.lower() not in resume_skills_lower:
            missing_skills.append(skill)
    
    return missing_skills

if __name__ == "__main__":
    # Example usage
    import sys
    import json
    from jobhuntgpt.job_fetcher import Job
    
    if len(sys.argv) < 3:
        print("Usage: python matcher.py <resume_json_path> <jobs_json_path> [top_k]")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    jobs_path = sys.argv[2]
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # Load resume
    with open(resume_path, 'r') as file:
        resume = json.load(file)
    
    # Load jobs
    with open(jobs_path, 'r') as file:
        job_dicts = json.load(file)
        jobs = [Job.from_dict(job_dict) for job_dict in job_dicts]
    
    # Rank jobs
    ranked_jobs = rank_jobs(resume, jobs, top_k)
    
    # Print results
    print(f"Top {len(ranked_jobs)} jobs for {resume.get('name', 'you')}:")
    for i, (job, similarity) in enumerate(ranked_jobs, 1):
        print(f"{i}. {job.title} at {job.company} - Match: {similarity:.2f}")
