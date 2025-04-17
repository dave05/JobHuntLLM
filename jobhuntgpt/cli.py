"""Command-line interface for JobHuntGPT."""

import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rich_print

from jobhuntgpt.resume_parser import parse_resume
from jobhuntgpt.job_fetcher import fetch_jobs, Job, save_jobs_to_json
from jobhuntgpt.matcher import rank_jobs
from jobhuntgpt.email_composer import compose_cover_letter, compose_followup
from jobhuntgpt.scheduler import schedule_application, schedule_followup
from jobhuntgpt.vector_index import build_or_load_index, query_index, save_resume_to_file, load_resume_from_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jobhuntgpt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(help="JobHuntGPT: An LLM-powered job search assistant")

# Create console for rich output
console = Console()

# Default paths
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_RESUME_PATH = "resume.pdf"
DEFAULT_JOBS_PATH = "jobs.json"
DEFAULT_INDEX_PATH = "index_data"
DEFAULT_OUTPUT_DIR = "output"

# Load configuration
def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        import yaml
        
        # Check if file exists
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
        
        # Load configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

# Command: parse
@app.command()
def parse(
    resume_path: str = typer.Option(DEFAULT_RESUME_PATH, "--resume", "-r", help="Path to the resume file"),
    output_path: str = typer.Option("resume.json", "--output", "-o", help="Path to save the parsed resume"),
    model_path: Optional[str] = typer.Option(None, "--model", "-m", help="Path to the LLaMA model")
):
    """Parse a resume and extract relevant information."""
    try:
        # Check if resume file exists
        if not os.path.exists(resume_path):
            console.print(f"[bold red]Error:[/bold red] Resume file not found: {resume_path}")
            raise typer.Exit(code=1)
        
        # Parse resume
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Parsing resume: {resume_path}", total=None)
            resume = parse_resume(resume_path, model_path)
        
        # Save parsed resume
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w') as file:
            json.dump(resume, file, indent=2)
        
        # Display parsed resume
        console.print(f"[bold green]Resume parsed successfully:[/bold green] {resume_path}")
        console.print(f"[bold green]Parsed resume saved to:[/bold green] {output_path}")
        
        # Display resume information
        table = Table(title=f"Resume: {resume.get('name', 'Unknown')}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Name", resume.get("name", ""))
        table.add_row("Email", resume.get("email", ""))
        table.add_row("Phone", resume.get("phone", ""))
        
        skills = resume.get("skills", [])
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        else:
            skills_str = str(skills)
        table.add_row("Skills", skills_str)
        
        experience = resume.get("experience", [])
        if isinstance(experience, list):
            experience_str = "\n".join([str(exp) for exp in experience])
        else:
            experience_str = str(experience)
        table.add_row("Experience", experience_str)
        
        education = resume.get("education", [])
        if isinstance(education, list):
            education_str = "\n".join([str(edu) for edu in education])
        else:
            education_str = str(education)
        table.add_row("Education", education_str)
        
        console.print(table)
        
        return resume
    except Exception as e:
        console.print(f"[bold red]Error parsing resume:[/bold red] {e}")
        logger.error(f"Error parsing resume: {e}")
        raise typer.Exit(code=1)

# Command: fetch
@app.command()
def fetch(
    source: str = typer.Option("csv", "--source", "-s", help="Source to fetch jobs from (linkedin, indeed, csv, json)"),
    query: str = typer.Option("software engineer", "--query", "-q", help="Job search query or file path"),
    location: str = typer.Option("remote", "--location", "-l", help="Job location"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of jobs to fetch"),
    output_path: str = typer.Option(DEFAULT_JOBS_PATH, "--output", "-o", help="Path to save the fetched jobs"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key for the source")
):
    """Fetch job listings from the specified source."""
    try:
        # Fetch jobs
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching jobs from {source}", total=None)
            jobs = fetch_jobs(source, query, location, limit, api_key)
        
        # Save fetched jobs
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        save_jobs_to_json(jobs, output_path)
        
        # Display fetched jobs
        console.print(f"[bold green]Jobs fetched successfully:[/bold green] {len(jobs)} jobs from {source}")
        console.print(f"[bold green]Jobs saved to:[/bold green] {output_path}")
        
        # Display job information
        table = Table(title=f"Fetched Jobs ({len(jobs)})")
        table.add_column("Title", style="cyan")
        table.add_column("Company", style="green")
        table.add_column("Location", style="yellow")
        table.add_column("Date Posted", style="blue")
        
        for job in jobs:
            table.add_row(job.title, job.company, job.location, job.date_posted)
        
        console.print(table)
        
        return jobs
    except Exception as e:
        console.print(f"[bold red]Error fetching jobs:[/bold red] {e}")
        logger.error(f"Error fetching jobs: {e}")
        raise typer.Exit(code=1)

# Command: rank
@app.command()
def rank(
    resume_path: str = typer.Option("resume.json", "--resume", "-r", help="Path to the parsed resume"),
    jobs_path: str = typer.Option(DEFAULT_JOBS_PATH, "--jobs", "-j", help="Path to the fetched jobs"),
    top_k: int = typer.Option(10, "--top", "-k", help="Number of top jobs to return"),
    model_name: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m", help="Name of the sentence transformer model"),
    output_path: str = typer.Option("ranked_jobs.json", "--output", "-o", help="Path to save the ranked jobs")
):
    """Rank jobs based on similarity to resume."""
    try:
        # Check if files exist
        if not os.path.exists(resume_path):
            console.print(f"[bold red]Error:[/bold red] Resume file not found: {resume_path}")
            raise typer.Exit(code=1)
        
        if not os.path.exists(jobs_path):
            console.print(f"[bold red]Error:[/bold red] Jobs file not found: {jobs_path}")
            raise typer.Exit(code=1)
        
        # Load resume
        with open(resume_path, 'r') as file:
            resume = json.load(file)
        
        # Load jobs
        with open(jobs_path, 'r') as file:
            job_dicts = json.load(file)
            jobs = [Job.from_dict(job_dict) for job_dict in job_dicts]
        
        # Rank jobs
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Ranking jobs", total=None)
            ranked_jobs = rank_jobs(resume, jobs, top_k, model_name)
        
        # Save ranked jobs
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w') as file:
            json.dump([{"job": job.to_dict(), "similarity": similarity} for job, similarity in ranked_jobs], file, indent=2)
        
        # Display ranked jobs
        console.print(f"[bold green]Jobs ranked successfully:[/bold green] {len(ranked_jobs)} jobs")
        console.print(f"[bold green]Ranked jobs saved to:[/bold green] {output_path}")
        
        # Display job information
        table = Table(title=f"Top {len(ranked_jobs)} Jobs for {resume.get('name', 'you')}")
        table.add_column("Rank", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Company", style="yellow")
        table.add_column("Match", style="blue")
        
        for i, (job, similarity) in enumerate(ranked_jobs, 1):
            table.add_row(str(i), job.title, job.company, f"{similarity:.2f}")
        
        console.print(table)
        
        return ranked_jobs
    except Exception as e:
        console.print(f"[bold red]Error ranking jobs:[/bold red] {e}")
        logger.error(f"Error ranking jobs: {e}")
        raise typer.Exit(code=1)

# Command: compose
@app.command()
def compose(
    resume_path: str = typer.Option("resume.json", "--resume", "-r", help="Path to the parsed resume"),
    job_path: str = typer.Option("job.json", "--job", "-j", help="Path to the job"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", "-o", help="Directory to save the composed emails"),
    model_path: Optional[str] = typer.Option(None, "--model", "-m", help="Path to the LLaMA model"),
    type: str = typer.Option("cover", "--type", "-t", help="Type of email to compose (cover, followup)")
):
    """Compose a cover letter or follow-up email for a job application."""
    try:
        # Check if files exist
        if not os.path.exists(resume_path):
            console.print(f"[bold red]Error:[/bold red] Resume file not found: {resume_path}")
            raise typer.Exit(code=1)
        
        if not os.path.exists(job_path):
            console.print(f"[bold red]Error:[/bold red] Job file not found: {job_path}")
            raise typer.Exit(code=1)
        
        # Load resume
        with open(resume_path, 'r') as file:
            resume = json.load(file)
        
        # Load job
        with open(job_path, 'r') as file:
            job_dict = json.load(file)
            if "job" in job_dict and "similarity" in job_dict:
                # Handle case where job is from ranked_jobs.json
                job = Job.from_dict(job_dict["job"])
            else:
                job = Job.from_dict(job_dict)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Compose email
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            if type.lower() == "cover":
                progress.add_task(description=f"Composing cover letter", total=None)
                email = compose_cover_letter(job, resume, model_path)
                output_path = os.path.join(output_dir, f"cover_letter_{job.company}.txt")
            elif type.lower() == "followup":
                # Check if cover letter exists
                cover_letter_path = os.path.join(output_dir, f"cover_letter_{job.company}.txt")
                if os.path.exists(cover_letter_path):
                    with open(cover_letter_path, 'r') as file:
                        previous_email = file.read()
                else:
                    previous_email = compose_cover_letter(job, resume, model_path)
                
                progress.add_task(description=f"Composing follow-up email", total=None)
                email = compose_followup(job, previous_email, 7, model_path)
                output_path = os.path.join(output_dir, f"followup_{job.company}.txt")
            else:
                console.print(f"[bold red]Error:[/bold red] Invalid email type: {type}")
                raise typer.Exit(code=1)
        
        # Save email
        with open(output_path, 'w') as file:
            file.write(email)
        
        # Display email
        console.print(f"[bold green]Email composed successfully:[/bold green] {type.lower()}")
        console.print(f"[bold green]Email saved to:[/bold green] {output_path}")
        console.print("\n" + email)
        
        return email
    except Exception as e:
        console.print(f"[bold red]Error composing email:[/bold red] {e}")
        logger.error(f"Error composing email: {e}")
        raise typer.Exit(code=1)

# Command: schedule
@app.command()
def schedule(
    job_path: str = typer.Option("job.json", "--job", "-j", help="Path to the job"),
    days_after: int = typer.Option(7, "--days", "-d", help="Number of days after the application to follow up"),
    use_google_calendar: bool = typer.Option(False, "--google", "-g", help="Use Google Calendar"),
    credentials_path: Optional[str] = typer.Option(None, "--credentials", "-c", help="Path to the Google Calendar credentials.json file"),
    token_path: Optional[str] = typer.Option(None, "--token", "-t", help="Path to save/load the Google Calendar token.pickle file"),
    job_data_dir: str = typer.Option("job_data", "--data-dir", "-o", help="Directory to save job data")
):
    """Schedule a follow-up for a job application."""
    try:
        # Check if job file exists
        if not os.path.exists(job_path):
            console.print(f"[bold red]Error:[/bold red] Job file not found: {job_path}")
            raise typer.Exit(code=1)
        
        # Load job
        with open(job_path, 'r') as file:
            job_dict = json.load(file)
            if "job" in job_dict and "similarity" in job_dict:
                # Handle case where job is from ranked_jobs.json
                job = Job.from_dict(job_dict["job"])
            else:
                job = Job.from_dict(job_dict)
        
        # Schedule application
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Scheduling application", total=None)
            application_id = schedule_application(
                job,
                use_google_calendar=use_google_calendar,
                credentials_path=credentials_path,
                token_path=token_path,
                job_data_dir=job_data_dir
            )
        
        # Schedule follow-up
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Scheduling follow-up", total=None)
            followup_id = schedule_followup(
                job,
                days_after=days_after,
                use_google_calendar=use_google_calendar,
                credentials_path=credentials_path,
                token_path=token_path,
                job_data_dir=job_data_dir
            )
        
        # Display scheduled events
        console.print(f"[bold green]Application scheduled successfully:[/bold green] {application_id}")
        console.print(f"[bold green]Follow-up scheduled successfully:[/bold green] {followup_id}")
        
        return {"application_id": application_id, "followup_id": followup_id}
    except Exception as e:
        console.print(f"[bold red]Error scheduling events:[/bold red] {e}")
        logger.error(f"Error scheduling events: {e}")
        raise typer.Exit(code=1)

# Command: query
@app.command()
def query(
    query_text: str = typer.Argument(..., help="Query text"),
    resume_path: str = typer.Option("resume.json", "--resume", "-r", help="Path to the parsed resume"),
    jobs_path: str = typer.Option(DEFAULT_JOBS_PATH, "--jobs", "-j", help="Path to the fetched jobs"),
    index_path: str = typer.Option(DEFAULT_INDEX_PATH, "--index", "-i", help="Path to the index directory"),
    model_path: Optional[str] = typer.Option(None, "--model", "-m", help="Path to the LLaMA model"),
    embedding_model: str = typer.Option("all-MiniLM-L6-v2", "--embedding", "-e", help="Name of the embedding model")
):
    """Query the vector index for information."""
    try:
        # Check if files exist
        if not os.path.exists(resume_path):
            console.print(f"[bold red]Error:[/bold red] Resume file not found: {resume_path}")
            raise typer.Exit(code=1)
        
        if not os.path.exists(jobs_path):
            console.print(f"[bold red]Error:[/bold red] Jobs file not found: {jobs_path}")
            raise typer.Exit(code=1)
        
        # Load resume
        with open(resume_path, 'r') as file:
            resume = json.load(file)
        
        # Load jobs
        with open(jobs_path, 'r') as file:
            job_dicts = json.load(file)
            jobs = [Job.from_dict(job_dict) for job_dict in job_dicts]
        
        # Build or load index
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Building or loading index", total=None)
            index = build_or_load_index(
                resume=resume,
                jobs=jobs,
                embedding_model_name=embedding_model,
                llm_model_path=model_path,
                persist_dir=index_path
            )
        
        # Query index
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Querying index", total=None)
            response = query_index(index, query_text, model_path)
        
        # Display response
        console.print(f"[bold green]Query:[/bold green] {query_text}")
        console.print(f"[bold green]Response:[/bold green] {response}")
        
        return response
    except Exception as e:
        console.print(f"[bold red]Error querying index:[/bold red] {e}")
        logger.error(f"Error querying index: {e}")
        raise typer.Exit(code=1)

# Command: run-all
@app.command()
def run_all(
    resume_path: str = typer.Option(DEFAULT_RESUME_PATH, "--resume", "-r", help="Path to the resume file"),
    source: str = typer.Option("csv", "--source", "-s", help="Source to fetch jobs from (linkedin, indeed, csv, json)"),
    query: str = typer.Option("software engineer", "--query", "-q", help="Job search query or file path"),
    location: str = typer.Option("remote", "--location", "-l", help="Job location"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of jobs to fetch"),
    top_k: int = typer.Option(5, "--top", "-k", help="Number of top jobs to return"),
    model_path: Optional[str] = typer.Option(None, "--model", "-m", help="Path to the LLaMA model"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", "-o", help="Directory to save output files"),
    schedule_followups: bool = typer.Option(False, "--schedule", "-f", help="Schedule follow-ups"),
    use_google_calendar: bool = typer.Option(False, "--google", "-g", help="Use Google Calendar"),
    credentials_path: Optional[str] = typer.Option(None, "--credentials", "-c", help="Path to the Google Calendar credentials.json file"),
    token_path: Optional[str] = typer.Option(None, "--token", "-t", help="Path to save/load the Google Calendar token.pickle file")
):
    """Run the complete job search workflow."""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Parse resume
        console.print("[bold cyan]Step 1: Parsing resume[/bold cyan]")
        parsed_resume_path = os.path.join(output_dir, "resume.json")
        resume = parse(resume_path, parsed_resume_path, model_path)
        
        # Step 2: Fetch jobs
        console.print("\n[bold cyan]Step 2: Fetching jobs[/bold cyan]")
        jobs_path = os.path.join(output_dir, "jobs.json")
        jobs = fetch(source, query, location, limit, jobs_path)
        
        # Step 3: Rank jobs
        console.print("\n[bold cyan]Step 3: Ranking jobs[/bold cyan]")
        ranked_jobs_path = os.path.join(output_dir, "ranked_jobs.json")
        ranked_jobs = rank(parsed_resume_path, jobs_path, top_k, "all-MiniLM-L6-v2", ranked_jobs_path)
        
        # Step 4: Compose cover letters for top jobs
        console.print("\n[bold cyan]Step 4: Composing cover letters[/bold cyan]")
        for i, (job, similarity) in enumerate(ranked_jobs[:top_k], 1):
            console.print(f"\n[bold cyan]Composing cover letter for job {i}/{top_k}:[/bold cyan] {job.title} at {job.company}")
            
            # Save job to file
            job_path = os.path.join(output_dir, f"job_{i}.json")
            with open(job_path, 'w') as file:
                json.dump({"job": job.to_dict(), "similarity": similarity}, file, indent=2)
            
            # Compose cover letter
            compose(parsed_resume_path, job_path, output_dir, model_path, "cover")
            
            # Schedule follow-up if requested
            if schedule_followups:
                console.print(f"\n[bold cyan]Scheduling follow-up for job {i}/{top_k}:[/bold cyan] {job.title} at {job.company}")
                schedule(job_path, 7, use_google_calendar, credentials_path, token_path, os.path.join(output_dir, "job_data"))
        
        console.print("\n[bold green]Job search workflow completed successfully![/bold green]")
        console.print(f"[bold green]Output files saved to:[/bold green] {output_dir}")
        
        return {"resume": resume, "jobs": jobs, "ranked_jobs": ranked_jobs}
    except Exception as e:
        console.print(f"[bold red]Error running workflow:[/bold red] {e}")
        logger.error(f"Error running workflow: {e}")
        raise typer.Exit(code=1)

# Callback functions for scheduler
def application_callback(job_data_path: str) -> None:
    """Callback function for application events."""
    try:
        # Load job data
        with open(job_data_path, 'r') as file:
            job_data = json.load(file)
        
        job = Job.from_dict(job_data["job"])
        
        # Log event
        logger.info(f"Application event triggered for {job.title} at {job.company}")
        
        # Print notification
        print(f"Reminder: Submit application for {job.title} at {job.company}")
    except Exception as e:
        logger.error(f"Error in application callback: {e}")

def followup_callback(job_data_path: str) -> None:
    """Callback function for follow-up events."""
    try:
        # Load job data
        with open(job_data_path, 'r') as file:
            job_data = json.load(file)
        
        job = Job.from_dict(job_data["job"])
        
        # Log event
        logger.info(f"Follow-up event triggered for {job.title} at {job.company}")
        
        # Print notification
        print(f"Reminder: Send follow-up email for {job.title} at {job.company}")
    except Exception as e:
        logger.error(f"Error in follow-up callback: {e}")

def interview_callback(job_data_path: str) -> None:
    """Callback function for interview events."""
    try:
        # Load job data
        with open(job_data_path, 'r') as file:
            job_data = json.load(file)
        
        job = Job.from_dict(job_data["job"])
        
        # Log event
        logger.info(f"Interview event triggered for {job.title} at {job.company}")
        
        # Print notification
        print(f"Reminder: Prepare for interview for {job.title} at {job.company}")
    except Exception as e:
        logger.error(f"Error in interview callback: {e}")

if __name__ == "__main__":
    app()
