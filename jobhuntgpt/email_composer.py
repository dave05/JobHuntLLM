"""Email composer module for JobHuntGPT."""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate

from jobhuntgpt.job_fetcher import Job
from jobhuntgpt.matcher import get_matching_skills

logger = logging.getLogger(__name__)

class EmailComposerError(Exception):
    """Exception raised for errors in the email composer."""
    pass

def initialize_llm(model_path: str) -> LlamaCpp:
    """
    Initialize LLaMA model.
    
    Args:
        model_path: Path to the LLaMA model
        
    Returns:
        Initialized LLaMA model
    """
    try:
        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Initialize LLaMA model
        llm = LlamaCpp(
            model_path=model_path,
            temperature=0.7,
            max_tokens=2048,
            n_ctx=4096,
            verbose=False
        )
        
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        raise EmailComposerError(f"Failed to initialize LLM: {e}")

def compose_cover_letter(job: Job, resume: Dict[str, Any], model_path: Optional[str] = None) -> str:
    """
    Compose a cover letter for a job application.
    
    Args:
        job: Job object
        resume: Dictionary containing parsed resume information
        model_path: Path to the LLaMA model (optional)
        
    Returns:
        Generated cover letter
    """
    try:
        # Extract information from resume
        name = resume.get("name", "")
        email = resume.get("email", "")
        phone = resume.get("phone", "")
        skills = resume.get("skills", [])
        experience = resume.get("experience", [])
        education = resume.get("education", [])
        
        # Get matching skills
        matching_skills = get_matching_skills(resume, job)
        
        # Format today's date
        today = datetime.now().strftime("%B %d, %Y")
        
        # If model_path is provided, use LLaMA model
        if model_path and os.path.exists(model_path):
            try:
                # Initialize LLaMA model
                llm = initialize_llm(model_path)
                
                # Create prompt template
                prompt = PromptTemplate(
                    input_variables=["name", "job_title", "company", "skills", "experience", "education", "matching_skills"],
                    template="""
                    Write a professional cover letter for {name} applying for the {job_title} position at {company}.
                    
                    The applicant has the following skills: {skills}
                    
                    The applicant's experience includes: {experience}
                    
                    The applicant's education includes: {education}
                    
                    The following skills from the applicant's resume match the job description: {matching_skills}
                    
                    Write a compelling cover letter that highlights the applicant's relevant skills and experience.
                    The letter should be professional, concise, and tailored to the specific job.
                    
                    Cover Letter:
                    """
                )
                
                # Format experience and education for the prompt
                experience_str = ", ".join([str(exp) for exp in experience])
                education_str = ", ".join([str(edu) for edu in education])
                skills_str = ", ".join(skills)
                matching_skills_str = ", ".join(matching_skills)
                
                # Generate cover letter
                cover_letter = llm(prompt.format(
                    name=name,
                    job_title=job.title,
                    company=job.company,
                    skills=skills_str,
                    experience=experience_str,
                    education=education_str,
                    matching_skills=matching_skills_str
                ))
                
                return cover_letter.strip()
            
            except Exception as e:
                logger.warning(f"Error generating cover letter with LLM: {e}")
                logger.warning("Falling back to template-based cover letter")
        
        # If no model_path or LLM generation failed, use template-based approach
        matching_skills_str = ", ".join(matching_skills) if matching_skills else "relevant skills and experience"
        
        # Create a template-based cover letter
        cover_letter = f"""
        {today}

        Dear Hiring Manager,

        I am writing to express my interest in the {job.title} position at {job.company}. With my background and skills in {matching_skills_str}, I believe I would be a valuable addition to your team.

        Throughout my career, I have developed expertise in {", ".join(skills[:5]) if skills else "various technical areas"}. My experience has prepared me to excel in this role and contribute to {job.company}'s success.

        I am particularly drawn to this opportunity because it aligns with my professional goals and allows me to leverage my strengths in {matching_skills_str}. I am confident that my skills and experience make me a strong candidate for this position.

        Thank you for considering my application. I look forward to the opportunity to discuss how my background and skills would benefit {job.company}.

        Sincerely,
        {name}
        {email}
        {phone}
        """
        
        return cover_letter.strip()
    
    except Exception as e:
        logger.error(f"Error composing cover letter: {e}")
        raise EmailComposerError(f"Failed to compose cover letter: {e}")

def compose_followup(job: Job, previous_email: str, days_since_application: int = 7, 
                     model_path: Optional[str] = None) -> str:
    """
    Compose a follow-up email for a job application.
    
    Args:
        job: Job object
        previous_email: Previous email or cover letter
        days_since_application: Number of days since the application was submitted
        model_path: Path to the LLaMA model (optional)
        
    Returns:
        Generated follow-up email
    """
    try:
        # Extract name from previous email (assuming it's at the end)
        lines = previous_email.strip().split('\n')
        name = lines[-3].strip() if len(lines) >= 3 else "Your Name"
        
        # Format today's date
        today = datetime.now().strftime("%B %d, %Y")
        
        # If model_path is provided, use LLaMA model
        if model_path and os.path.exists(model_path):
            try:
                # Initialize LLaMA model
                llm = initialize_llm(model_path)
                
                # Create prompt template
                prompt = PromptTemplate(
                    input_variables=["name", "job_title", "company", "days_since_application", "previous_email"],
                    template="""
                    Write a professional follow-up email for {name} who applied for the {job_title} position at {company} {days_since_application} days ago.
                    
                    The applicant's original application/cover letter was:
                    
                    {previous_email}
                    
                    Write a polite and concise follow-up email that:
                    1. References the original application
                    2. Expresses continued interest in the position
                    3. Asks about the status of the application
                    4. Offers to provide any additional information
                    
                    Follow-up Email:
                    """
                )
                
                # Generate follow-up email
                followup_email = llm(prompt.format(
                    name=name,
                    job_title=job.title,
                    company=job.company,
                    days_since_application=days_since_application,
                    previous_email=previous_email
                ))
                
                return followup_email.strip()
            
            except Exception as e:
                logger.warning(f"Error generating follow-up email with LLM: {e}")
                logger.warning("Falling back to template-based follow-up email")
        
        # If no model_path or LLM generation failed, use template-based approach
        
        # Create a template-based follow-up email
        followup_email = f"""
        {today}

        Dear Hiring Manager,

        I hope this email finds you well. I am writing to follow up on my application for the {job.title} position at {job.company}, which I submitted {days_since_application} days ago.

        I remain very interested in this opportunity and would appreciate any update you can provide regarding the status of my application. If you need any additional information or would like to schedule an interview, please don't hesitate to contact me.

        Thank you for your time and consideration. I look forward to hearing from you.

        Sincerely,
        {name}
        """
        
        return followup_email.strip()
    
    except Exception as e:
        logger.error(f"Error composing follow-up email: {e}")
        raise EmailComposerError(f"Failed to compose follow-up email: {e}")

def compose_thank_you(job: Job, interviewer_name: str, interview_notes: str = "", 
                      model_path: Optional[str] = None) -> str:
    """
    Compose a thank you email after an interview.
    
    Args:
        job: Job object
        interviewer_name: Name of the interviewer
        interview_notes: Notes from the interview (optional)
        model_path: Path to the LLaMA model (optional)
        
    Returns:
        Generated thank you email
    """
    try:
        # Format today's date
        today = datetime.now().strftime("%B %d, %Y")
        
        # If model_path is provided, use LLaMA model
        if model_path and os.path.exists(model_path):
            try:
                # Initialize LLaMA model
                llm = initialize_llm(model_path)
                
                # Create prompt template
                prompt = PromptTemplate(
                    input_variables=["interviewer_name", "job_title", "company", "interview_notes"],
                    template="""
                    Write a professional thank you email to {interviewer_name} after an interview for the {job_title} position at {company}.
                    
                    Notes from the interview:
                    {interview_notes}
                    
                    Write a polite and concise thank you email that:
                    1. Thanks the interviewer for their time
                    2. References specific topics discussed in the interview
                    3. Reiterates interest in the position
                    4. Mentions looking forward to the next steps
                    
                    Thank You Email:
                    """
                )
                
                # Generate thank you email
                thank_you_email = llm(prompt.format(
                    interviewer_name=interviewer_name,
                    job_title=job.title,
                    company=job.company,
                    interview_notes=interview_notes
                ))
                
                return thank_you_email.strip()
            
            except Exception as e:
                logger.warning(f"Error generating thank you email with LLM: {e}")
                logger.warning("Falling back to template-based thank you email")
        
        # If no model_path or LLM generation failed, use template-based approach
        
        # Create a template-based thank you email
        specific_topic = "our discussion about the role" if not interview_notes else "our discussion about " + interview_notes.split()[0:5]
        
        thank_you_email = f"""
        {today}

        Dear {interviewer_name},

        Thank you for taking the time to interview me for the {job.title} position at {job.company}. I enjoyed our conversation and appreciated the opportunity to learn more about the role and the company.

        I was particularly interested in {specific_topic} and am excited about the possibility of contributing to your team.

        After our discussion, I am even more enthusiastic about the position and confident that my skills and experience align well with what you're looking for.

        Thank you again for your consideration. I look forward to hearing about the next steps in the process.

        Sincerely,
        [Your Name]
        """
        
        return thank_you_email.strip()
    
    except Exception as e:
        logger.error(f"Error composing thank you email: {e}")
        raise EmailComposerError(f"Failed to compose thank you email: {e}")

if __name__ == "__main__":
    # Example usage
    import sys
    import json
    from jobhuntgpt.job_fetcher import Job
    
    if len(sys.argv) < 3:
        print("Usage: python email_composer.py <resume_json_path> <job_json_path> [model_path]")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    job_path = sys.argv[2]
    model_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load resume
    with open(resume_path, 'r') as file:
        resume = json.load(file)
    
    # Load job
    with open(job_path, 'r') as file:
        job_dict = json.load(file)
        job = Job.from_dict(job_dict)
    
    # Generate cover letter
    cover_letter = compose_cover_letter(job, resume, model_path)
    print("Cover Letter:")
    print(cover_letter)
    print("\n" + "-" * 50 + "\n")
    
    # Generate follow-up email
    followup_email = compose_followup(job, cover_letter, 7, model_path)
    print("Follow-up Email:")
    print(followup_email)
