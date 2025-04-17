"""Scheduler module for JobHuntGPT."""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pickle

# Google Calendar API
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logging.warning("Google API libraries not available, falling back to local scheduler")

# APScheduler for local scheduling
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger

from jobhuntgpt.job_fetcher import Job

logger = logging.getLogger(__name__)

class SchedulerError(Exception):
    """Exception raised for errors in the scheduler."""
    pass

# Initialize APScheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def authenticate_google_calendar(credentials_path: str, token_path: str, scopes: List[str]) -> Any:
    """
    Authenticate with Google Calendar API.
    
    Args:
        credentials_path: Path to the credentials.json file
        token_path: Path to save/load the token.pickle file
        scopes: List of API scopes
        
    Returns:
        Authenticated Google Calendar service
    """
    creds = None
    
    # Check if token.pickle exists
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are invalid or don't exist, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build the service
    service = build('calendar', 'v3', credentials=creds)
    
    return service

def schedule_with_google_calendar(job: Job, event_type: str, event_date: datetime, 
                                 credentials_path: str, token_path: str) -> str:
    """
    Schedule an event with Google Calendar.
    
    Args:
        job: Job object
        event_type: Type of event (application, followup, interview)
        event_date: Date and time of the event
        credentials_path: Path to the credentials.json file
        token_path: Path to save/load the token.pickle file
        
    Returns:
        Event ID
    """
    try:
        # Check if Google API is available
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not available")
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        # Authenticate with Google Calendar API
        scopes = ['https://www.googleapis.com/auth/calendar']
        service = authenticate_google_calendar(credentials_path, token_path, scopes)
        
        # Create event details based on event type
        if event_type == "application":
            summary = f"Job Application: {job.title} at {job.company}"
            description = f"Submit job application for {job.title} position at {job.company}.\n\nJob URL: {job.url}"
        elif event_type == "followup":
            summary = f"Follow-up: {job.title} at {job.company}"
            description = f"Send follow-up email for {job.title} position at {job.company}.\n\nJob URL: {job.url}"
        elif event_type == "interview":
            summary = f"Interview: {job.title} at {job.company}"
            description = f"Interview for {job.title} position at {job.company}.\n\nJob URL: {job.url}"
        else:
            summary = f"Job Hunt: {job.title} at {job.company}"
            description = f"Event related to {job.title} position at {job.company}.\n\nJob URL: {job.url}"
        
        # Format event date
        start_time = event_date.isoformat()
        end_time = (event_date + timedelta(hours=1)).isoformat()
        
        # Create event
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Los_Angeles',  # TODO: Make this configurable
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Los_Angeles',  # TODO: Make this configurable
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 30},  # 30 minutes before
                ],
            },
        }
        
        # Add event to calendar
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        logger.info(f"Event created: {event.get('htmlLink')}")
        
        return event.get('id')
    
    except Exception as e:
        logger.error(f"Error scheduling with Google Calendar: {e}")
        raise SchedulerError(f"Failed to schedule with Google Calendar: {e}")

def schedule_with_apscheduler(job: Job, event_type: str, event_date: datetime, 
                             callback_function: str, job_data_path: str) -> str:
    """
    Schedule an event with APScheduler.
    
    Args:
        job: Job object
        event_type: Type of event (application, followup, interview)
        event_date: Date and time of the event
        callback_function: Name of the function to call when the event is triggered
        job_data_path: Path to save the job data
        
    Returns:
        Job ID
    """
    try:
        # Save job data to file
        job_data = {
            "job": job.to_dict(),
            "event_type": event_type,
            "event_date": event_date.isoformat(),
            "callback_function": callback_function
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(job_data_path), exist_ok=True)
        
        with open(job_data_path, 'w') as file:
            json.dump(job_data, file)
        
        # Define the job function
        def job_function():
            logger.info(f"Executing scheduled job: {event_type} for {job.title} at {job.company}")
            logger.info(f"Job data saved at: {job_data_path}")
            # The actual callback would be implemented by the user
        
        # Schedule the job
        job_id = f"{event_type}_{job.company}_{event_date.strftime('%Y%m%d%H%M%S')}"
        scheduler.add_job(
            job_function,
            trigger=DateTrigger(run_date=event_date),
            id=job_id,
            name=f"{event_type}: {job.title} at {job.company}",
            replace_existing=True
        )
        
        logger.info(f"Job scheduled: {job_id} at {event_date}")
        
        return job_id
    
    except Exception as e:
        logger.error(f"Error scheduling with APScheduler: {e}")
        raise SchedulerError(f"Failed to schedule with APScheduler: {e}")

def schedule_application(job: Job, application_date: Optional[datetime] = None, 
                        use_google_calendar: bool = False, credentials_path: str = None, 
                        token_path: str = None, callback_function: str = None, 
                        job_data_dir: str = "job_data") -> str:
    """
    Schedule a job application.
    
    Args:
        job: Job object
        application_date: Date and time of the application (default: now)
        use_google_calendar: Whether to use Google Calendar (default: False)
        credentials_path: Path to the credentials.json file (required if use_google_calendar is True)
        token_path: Path to save/load the token.pickle file (required if use_google_calendar is True)
        callback_function: Name of the function to call when the event is triggered (required if use_google_calendar is False)
        job_data_dir: Directory to save job data (required if use_google_calendar is False)
        
    Returns:
        Event/Job ID
    """
    # Set application date to now if not provided
    if application_date is None:
        application_date = datetime.now()
    
    # Schedule with Google Calendar if requested and available
    if use_google_calendar and GOOGLE_API_AVAILABLE:
        if not credentials_path or not token_path:
            raise ValueError("credentials_path and token_path are required for Google Calendar")
        
        return schedule_with_google_calendar(job, "application", application_date, credentials_path, token_path)
    
    # Otherwise, schedule with APScheduler
    if not callback_function:
        callback_function = "jobhuntgpt.cli.application_callback"
    
    job_data_path = os.path.join(job_data_dir, f"application_{job.company}_{application_date.strftime('%Y%m%d%H%M%S')}.json")
    
    return schedule_with_apscheduler(job, "application", application_date, callback_function, job_data_path)

def schedule_followup(job: Job, days_after: int = 7, application_date: Optional[datetime] = None, 
                     use_google_calendar: bool = False, credentials_path: str = None, 
                     token_path: str = None, callback_function: str = None, 
                     job_data_dir: str = "job_data") -> str:
    """
    Schedule a follow-up for a job application.
    
    Args:
        job: Job object
        days_after: Number of days after the application to follow up
        application_date: Date and time of the application (default: now)
        use_google_calendar: Whether to use Google Calendar (default: False)
        credentials_path: Path to the credentials.json file (required if use_google_calendar is True)
        token_path: Path to save/load the token.pickle file (required if use_google_calendar is True)
        callback_function: Name of the function to call when the event is triggered (required if use_google_calendar is False)
        job_data_dir: Directory to save job data (required if use_google_calendar is False)
        
    Returns:
        Event/Job ID
    """
    # Set application date to now if not provided
    if application_date is None:
        application_date = datetime.now()
    
    # Calculate follow-up date
    followup_date = application_date + timedelta(days=days_after)
    
    # Schedule with Google Calendar if requested and available
    if use_google_calendar and GOOGLE_API_AVAILABLE:
        if not credentials_path or not token_path:
            raise ValueError("credentials_path and token_path are required for Google Calendar")
        
        return schedule_with_google_calendar(job, "followup", followup_date, credentials_path, token_path)
    
    # Otherwise, schedule with APScheduler
    if not callback_function:
        callback_function = "jobhuntgpt.cli.followup_callback"
    
    job_data_path = os.path.join(job_data_dir, f"followup_{job.company}_{followup_date.strftime('%Y%m%d%H%M%S')}.json")
    
    return schedule_with_apscheduler(job, "followup", followup_date, callback_function, job_data_path)

def schedule_interview(job: Job, interview_date: datetime, 
                      use_google_calendar: bool = False, credentials_path: str = None, 
                      token_path: str = None, callback_function: str = None, 
                      job_data_dir: str = "job_data") -> str:
    """
    Schedule an interview for a job application.
    
    Args:
        job: Job object
        interview_date: Date and time of the interview
        use_google_calendar: Whether to use Google Calendar (default: False)
        credentials_path: Path to the credentials.json file (required if use_google_calendar is True)
        token_path: Path to save/load the token.pickle file (required if use_google_calendar is True)
        callback_function: Name of the function to call when the event is triggered (required if use_google_calendar is False)
        job_data_dir: Directory to save job data (required if use_google_calendar is False)
        
    Returns:
        Event/Job ID
    """
    # Schedule with Google Calendar if requested and available
    if use_google_calendar and GOOGLE_API_AVAILABLE:
        if not credentials_path or not token_path:
            raise ValueError("credentials_path and token_path are required for Google Calendar")
        
        return schedule_with_google_calendar(job, "interview", interview_date, credentials_path, token_path)
    
    # Otherwise, schedule with APScheduler
    if not callback_function:
        callback_function = "jobhuntgpt.cli.interview_callback"
    
    job_data_path = os.path.join(job_data_dir, f"interview_{job.company}_{interview_date.strftime('%Y%m%d%H%M%S')}.json")
    
    return schedule_with_apscheduler(job, "interview", interview_date, callback_function, job_data_path)

def list_scheduled_events(use_google_calendar: bool = False, credentials_path: str = None, 
                         token_path: str = None) -> List[Dict[str, Any]]:
    """
    List all scheduled events.
    
    Args:
        use_google_calendar: Whether to use Google Calendar (default: False)
        credentials_path: Path to the credentials.json file (required if use_google_calendar is True)
        token_path: Path to save/load the token.pickle file (required if use_google_calendar is True)
        
    Returns:
        List of scheduled events
    """
    try:
        # List events from Google Calendar if requested and available
        if use_google_calendar and GOOGLE_API_AVAILABLE:
            if not credentials_path or not token_path:
                raise ValueError("credentials_path and token_path are required for Google Calendar")
            
            # Authenticate with Google Calendar API
            scopes = ['https://www.googleapis.com/auth/calendar']
            service = authenticate_google_calendar(credentials_path, token_path, scopes)
            
            # Get events from calendar
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = []
            for event in events:
                # Check if this is a job hunt event
                if 'Job Application:' in event.get('summary', '') or 'Follow-up:' in event.get('summary', '') or 'Interview:' in event.get('summary', ''):
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    formatted_events.append({
                        'id': event['id'],
                        'summary': event['summary'],
                        'description': event.get('description', ''),
                        'start': start,
                        'link': event.get('htmlLink', '')
                    })
            
            return formatted_events
        
        # Otherwise, list jobs from APScheduler
        jobs = scheduler.get_jobs()
        
        # Format jobs
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return formatted_jobs
    
    except Exception as e:
        logger.error(f"Error listing scheduled events: {e}")
        raise SchedulerError(f"Failed to list scheduled events: {e}")

def remove_scheduled_event(event_id: str, use_google_calendar: bool = False, 
                          credentials_path: str = None, token_path: str = None) -> bool:
    """
    Remove a scheduled event.
    
    Args:
        event_id: ID of the event to remove
        use_google_calendar: Whether to use Google Calendar (default: False)
        credentials_path: Path to the credentials.json file (required if use_google_calendar is True)
        token_path: Path to save/load the token.pickle file (required if use_google_calendar is True)
        
    Returns:
        True if the event was removed, False otherwise
    """
    try:
        # Remove event from Google Calendar if requested and available
        if use_google_calendar and GOOGLE_API_AVAILABLE:
            if not credentials_path or not token_path:
                raise ValueError("credentials_path and token_path are required for Google Calendar")
            
            # Authenticate with Google Calendar API
            scopes = ['https://www.googleapis.com/auth/calendar']
            service = authenticate_google_calendar(credentials_path, token_path, scopes)
            
            # Delete event
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            logger.info(f"Event removed from Google Calendar: {event_id}")
            
            return True
        
        # Otherwise, remove job from APScheduler
        scheduler.remove_job(event_id)
        
        logger.info(f"Job removed from APScheduler: {event_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error removing scheduled event: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    import sys
    from jobhuntgpt.job_fetcher import Job
    
    # Create a sample job
    job = Job(
        title="Software Engineer",
        company="Example Company",
        location="Remote",
        description="Example job description",
        url="https://example.com/job",
        date_posted=datetime.now().strftime("%Y-%m-%d"),
        source="example"
    )
    
    # Schedule application and follow-up
    application_id = schedule_application(job, job_data_dir="job_data")
    followup_id = schedule_followup(job, days_after=7, job_data_dir="job_data")
    
    print(f"Application scheduled: {application_id}")
    print(f"Follow-up scheduled: {followup_id}")
    
    # List scheduled events
    events = list_scheduled_events()
    print("\nScheduled events:")
    for event in events:
        print(f"- {event['name']} at {event['next_run_time']}")
