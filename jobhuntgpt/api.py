"""API endpoints for JobHuntGPT."""

import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from jobhuntgpt.resume_parser import parse_resume
from jobhuntgpt.job_fetcher import fetch_jobs, Job, save_jobs_to_json
from jobhuntgpt.matcher import rank_jobs
from jobhuntgpt.email_composer import compose_cover_letter, compose_followup
from jobhuntgpt.scheduler import schedule_application, schedule_followup
from jobhuntgpt.vector_index import build_or_load_index, query_index, save_resume_to_file, load_resume_from_file
from jobhuntgpt.utils import load_config, get_config_value, save_json, load_json, create_directory_if_not_exists

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jobhuntgpt_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="JobHuntGPT API",
    description="API for JobHuntGPT, an LLM-powered job search assistant",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # In production, use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User database (in-memory for demo, use a real database in production)
users_db = {}

# Data directories
DATA_DIR = Path("data")
RESUME_DIR = DATA_DIR / "resumes"
JOBS_DIR = DATA_DIR / "jobs"
OUTPUT_DIR = DATA_DIR / "output"
INDEX_DIR = DATA_DIR / "index"

# Create directories
for directory in [DATA_DIR, RESUME_DIR, JOBS_DIR, OUTPUT_DIR, INDEX_DIR]:
    create_directory_if_not_exists(str(directory))

# Models
class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ResumeRequest(BaseModel):
    resume_text: Optional[str] = None
    model_path: Optional[str] = None

class JobFetchRequest(BaseModel):
    source: str = "csv"
    query: str = "software engineer"
    location: str = "remote"
    limit: int = 10
    api_key: Optional[str] = None

class JobRankRequest(BaseModel):
    resume_id: str
    jobs_id: str
    top_k: int = 10
    model_name: str = "all-MiniLM-L6-v2"

class EmailComposeRequest(BaseModel):
    resume_id: str
    job_id: str
    email_type: str = "cover"
    model_path: Optional[str] = None

class ScheduleRequest(BaseModel):
    job_id: str
    days_after: int = 7
    use_google_calendar: bool = False
    credentials_path: Optional[str] = None
    token_path: Optional[str] = None

class QueryRequest(BaseModel):
    query_text: str
    resume_id: str
    jobs_id: str
    model_path: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"

class RunAllRequest(BaseModel):
    resume_id: str
    source: str = "csv"
    query: str = "software engineer"
    location: str = "remote"
    limit: int = 10
    top_k: int = 5
    model_path: Optional[str] = None
    schedule_followups: bool = False

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

# Helper functions
def get_user(username: str) -> Optional[UserInDB]:
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_user_dir(username: str) -> Path:
    """Get the user's data directory."""
    user_dir = DATA_DIR / username
    create_directory_if_not_exists(str(user_dir))
    create_directory_if_not_exists(str(user_dir / "resumes"))
    create_directory_if_not_exists(str(user_dir / "jobs"))
    create_directory_if_not_exists(str(user_dir / "output"))
    create_directory_if_not_exists(str(user_dir / "index"))
    return user_dir

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    user_dict["disabled"] = False
    
    users_db[user.username] = user_dict
    
    # Create user directory
    get_user_dir(user.username)
    
    return user_dict

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/resume/parse")
async def parse_resume_endpoint(
    background_tasks: BackgroundTasks,
    resume_file: UploadFile = File(None),
    resume_text: str = Form(None),
    model_path: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Handle file upload or text input
        if resume_file:
            # Save uploaded file
            resume_path = user_dir / "resumes" / resume_file.filename
            with open(resume_path, "wb") as f:
                f.write(await resume_file.read())
        elif resume_text:
            # Save text to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(resume_text)
                resume_path = Path(f.name)
        else:
            raise HTTPException(status_code=400, detail="Either resume_file or resume_text must be provided")
        
        # Parse resume
        resume = parse_resume(str(resume_path), model_path)
        
        # Generate ID for the resume
        resume_id = f"{current_user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save parsed resume
        resume_output_path = user_dir / "resumes" / f"{resume_id}.json"
        with open(resume_output_path, "w") as f:
            json.dump(resume, f, indent=2)
        
        # Clean up temporary file if created
        if resume_text and not resume_file:
            background_tasks.add_task(os.unlink, resume_path)
        
        return {
            "resume_id": resume_id,
            "resume": resume,
            "message": "Resume parsed successfully"
        }
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@app.post("/jobs/fetch")
async def fetch_jobs_endpoint(
    request: JobFetchRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Fetch jobs
        jobs = fetch_jobs(
            source=request.source,
            query=request.query,
            location=request.location,
            limit=request.limit,
            api_key=request.api_key
        )
        
        # Generate ID for the jobs
        jobs_id = f"{current_user.username}_{request.source}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save fetched jobs
        jobs_output_path = user_dir / "jobs" / f"{jobs_id}.json"
        save_jobs_to_json(jobs, str(jobs_output_path))
        
        return {
            "jobs_id": jobs_id,
            "jobs": [job.to_dict() for job in jobs],
            "message": f"Fetched {len(jobs)} jobs successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.post("/jobs/rank")
async def rank_jobs_endpoint(
    request: JobRankRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Load resume
        resume_path = user_dir / "resumes" / f"{request.resume_id}.json"
        if not resume_path.exists():
            raise HTTPException(status_code=404, detail=f"Resume with ID {request.resume_id} not found")
        
        with open(resume_path, "r") as f:
            resume = json.load(f)
        
        # Load jobs
        jobs_path = user_dir / "jobs" / f"{request.jobs_id}.json"
        if not jobs_path.exists():
            raise HTTPException(status_code=404, detail=f"Jobs with ID {request.jobs_id} not found")
        
        with open(jobs_path, "r") as f:
            job_dicts = json.load(f)
            jobs = [Job.from_dict(job_dict) for job_dict in job_dicts]
        
        # Rank jobs
        ranked_jobs = rank_jobs(
            resume=resume,
            jobs=jobs,
            top_k=request.top_k,
            model_name=request.model_name
        )
        
        # Generate ID for the ranked jobs
        ranked_jobs_id = f"{current_user.username}_ranked_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save ranked jobs
        ranked_jobs_output_path = user_dir / "output" / f"{ranked_jobs_id}.json"
        with open(ranked_jobs_output_path, "w") as f:
            json.dump([{"job": job.to_dict(), "similarity": similarity} for job, similarity in ranked_jobs], f, indent=2)
        
        return {
            "ranked_jobs_id": ranked_jobs_id,
            "ranked_jobs": [{"job": job.to_dict(), "similarity": similarity} for job, similarity in ranked_jobs],
            "message": f"Ranked {len(ranked_jobs)} jobs successfully"
        }
    except Exception as e:
        logger.error(f"Error ranking jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error ranking jobs: {str(e)}")

@app.post("/email/compose")
async def compose_email_endpoint(
    request: EmailComposeRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Load resume
        resume_path = user_dir / "resumes" / f"{request.resume_id}.json"
        if not resume_path.exists():
            raise HTTPException(status_code=404, detail=f"Resume with ID {request.resume_id} not found")
        
        with open(resume_path, "r") as f:
            resume = json.load(f)
        
        # Load job
        job_path = user_dir / "output" / f"{request.job_id}.json"
        if not job_path.exists():
            # Try looking in jobs directory
            job_path = user_dir / "jobs" / f"{request.job_id}.json"
            if not job_path.exists():
                raise HTTPException(status_code=404, detail=f"Job with ID {request.job_id} not found")
        
        with open(job_path, "r") as f:
            job_data = json.load(f)
            if isinstance(job_data, list):
                # Handle case where job_id points to a list of jobs
                job_dict = job_data[0]
            elif "job" in job_data and "similarity" in job_data:
                # Handle case where job_id points to a ranked job
                job_dict = job_data["job"]
            else:
                # Handle case where job_id points to a single job
                job_dict = job_data
            
            job = Job.from_dict(job_dict)
        
        # Compose email
        if request.email_type.lower() == "cover":
            email = compose_cover_letter(job, resume, request.model_path)
            email_type = "cover_letter"
        elif request.email_type.lower() == "followup":
            # Check if cover letter exists
            cover_letter_path = user_dir / "output" / f"cover_letter_{job.company}.txt"
            if cover_letter_path.exists():
                with open(cover_letter_path, "r") as f:
                    previous_email = f.read()
            else:
                previous_email = compose_cover_letter(job, resume, request.model_path)
            
            email = compose_followup(job, previous_email, 7, request.model_path)
            email_type = "followup"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid email type: {request.email_type}")
        
        # Generate ID for the email
        email_id = f"{current_user.username}_{email_type}_{job.company}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save email
        email_output_path = user_dir / "output" / f"{email_id}.txt"
        with open(email_output_path, "w") as f:
            f.write(email)
        
        return {
            "email_id": email_id,
            "email": email,
            "message": f"Email composed successfully"
        }
    except Exception as e:
        logger.error(f"Error composing email: {e}")
        raise HTTPException(status_code=500, detail=f"Error composing email: {str(e)}")

@app.post("/schedule")
async def schedule_endpoint(
    request: ScheduleRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Load job
        job_path = user_dir / "output" / f"{request.job_id}.json"
        if not job_path.exists():
            # Try looking in jobs directory
            job_path = user_dir / "jobs" / f"{request.job_id}.json"
            if not job_path.exists():
                raise HTTPException(status_code=404, detail=f"Job with ID {request.job_id} not found")
        
        with open(job_path, "r") as f:
            job_data = json.load(f)
            if isinstance(job_data, list):
                # Handle case where job_id points to a list of jobs
                job_dict = job_data[0]
            elif "job" in job_data and "similarity" in job_data:
                # Handle case where job_id points to a ranked job
                job_dict = job_data["job"]
            else:
                # Handle case where job_id points to a single job
                job_dict = job_data
            
            job = Job.from_dict(job_dict)
        
        # Create job data directory
        job_data_dir = user_dir / "output" / "job_data"
        create_directory_if_not_exists(str(job_data_dir))
        
        # Schedule application
        application_id = schedule_application(
            job=job,
            use_google_calendar=request.use_google_calendar,
            credentials_path=request.credentials_path,
            token_path=request.token_path,
            job_data_dir=str(job_data_dir)
        )
        
        # Schedule follow-up
        followup_id = schedule_followup(
            job=job,
            days_after=request.days_after,
            use_google_calendar=request.use_google_calendar,
            credentials_path=request.credentials_path,
            token_path=request.token_path,
            job_data_dir=str(job_data_dir)
        )
        
        return {
            "application_id": application_id,
            "followup_id": followup_id,
            "message": "Events scheduled successfully"
        }
    except Exception as e:
        logger.error(f"Error scheduling events: {e}")
        raise HTTPException(status_code=500, detail=f"Error scheduling events: {str(e)}")

@app.post("/query")
async def query_endpoint(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Load resume
        resume_path = user_dir / "resumes" / f"{request.resume_id}.json"
        if not resume_path.exists():
            raise HTTPException(status_code=404, detail=f"Resume with ID {request.resume_id} not found")
        
        with open(resume_path, "r") as f:
            resume = json.load(f)
        
        # Load jobs
        jobs_path = user_dir / "jobs" / f"{request.jobs_id}.json"
        if not jobs_path.exists():
            raise HTTPException(status_code=404, detail=f"Jobs with ID {request.jobs_id} not found")
        
        with open(jobs_path, "r") as f:
            job_dicts = json.load(f)
            jobs = [Job.from_dict(job_dict) for job_dict in job_dicts]
        
        # Create index directory
        index_dir = user_dir / "index" / f"{request.resume_id}_{request.jobs_id}"
        create_directory_if_not_exists(str(index_dir))
        
        # Build or load index
        index = build_or_load_index(
            resume=resume,
            jobs=jobs,
            embedding_model_name=request.embedding_model,
            llm_model_path=request.model_path,
            persist_dir=str(index_dir)
        )
        
        # Query index
        response = query_index(index, request.query_text, request.model_path)
        
        return {
            "query": request.query_text,
            "response": response,
            "message": "Query executed successfully"
        }
    except Exception as e:
        logger.error(f"Error querying index: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying index: {str(e)}")

@app.post("/run-all")
async def run_all_endpoint(
    request: RunAllRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_dir = get_user_dir(current_user.username)
        
        # Load resume
        resume_path = user_dir / "resumes" / f"{request.resume_id}.json"
        if not resume_path.exists():
            raise HTTPException(status_code=404, detail=f"Resume with ID {request.resume_id} not found")
        
        with open(resume_path, "r") as f:
            resume = json.load(f)
        
        # Fetch jobs
        jobs = fetch_jobs(
            source=request.source,
            query=request.query,
            location=request.location,
            limit=request.limit
        )
        
        # Generate ID for the jobs
        jobs_id = f"{current_user.username}_{request.source}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save fetched jobs
        jobs_output_path = user_dir / "jobs" / f"{jobs_id}.json"
        save_jobs_to_json(jobs, str(jobs_output_path))
        
        # Rank jobs
        ranked_jobs = rank_jobs(
            resume=resume,
            jobs=jobs,
            top_k=request.top_k,
            model_name="all-MiniLM-L6-v2"
        )
        
        # Generate ID for the ranked jobs
        ranked_jobs_id = f"{current_user.username}_ranked_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save ranked jobs
        ranked_jobs_output_path = user_dir / "output" / f"{ranked_jobs_id}.json"
        with open(ranked_jobs_output_path, "w") as f:
            json.dump([{"job": job.to_dict(), "similarity": similarity} for job, similarity in ranked_jobs], f, indent=2)
        
        # Compose cover letters for top jobs
        cover_letters = []
        for i, (job, similarity) in enumerate(ranked_jobs[:request.top_k], 1):
            # Save job to file
            job_id = f"{current_user.username}_job_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            job_path = user_dir / "output" / f"{job_id}.json"
            with open(job_path, "w") as f:
                json.dump({"job": job.to_dict(), "similarity": similarity}, f, indent=2)
            
            # Compose cover letter
            email = compose_cover_letter(job, resume, request.model_path)
            
            # Generate ID for the email
            email_id = f"{current_user.username}_cover_letter_{job.company}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Save email
            email_output_path = user_dir / "output" / f"{email_id}.txt"
            with open(email_output_path, "w") as f:
                f.write(email)
            
            cover_letters.append({
                "job_id": job_id,
                "email_id": email_id,
                "job": job.to_dict(),
                "similarity": similarity,
                "email": email
            })
            
            # Schedule follow-up if requested
            if request.schedule_followups:
                # Create job data directory
                job_data_dir = user_dir / "output" / "job_data"
                create_directory_if_not_exists(str(job_data_dir))
                
                # Schedule application and follow-up
                schedule_application(
                    job=job,
                    job_data_dir=str(job_data_dir)
                )
                
                schedule_followup(
                    job=job,
                    days_after=7,
                    job_data_dir=str(job_data_dir)
                )
        
        return {
            "resume_id": request.resume_id,
            "jobs_id": jobs_id,
            "ranked_jobs_id": ranked_jobs_id,
            "cover_letters": cover_letters,
            "message": "Workflow completed successfully"
        }
    except Exception as e:
        logger.error(f"Error running workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Error running workflow: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
