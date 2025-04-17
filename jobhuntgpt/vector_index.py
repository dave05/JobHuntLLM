"""Vector index module for JobHuntGPT."""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import json

from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Document,
    ServiceContext,
    StorageContext,
    load_index_from_storage
)
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.llms import LlamaCPP
from llama_index.node_parser import SimpleNodeParser

from jobhuntgpt.job_fetcher import Job

logger = logging.getLogger(__name__)

class VectorIndexError(Exception):
    """Exception raised for errors in the vector index."""
    pass

def initialize_llm(model_path: str) -> LlamaCPP:
    """
    Initialize LLaMA model for llama_index.
    
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
        llm = LlamaCPP(
            model_path=model_path,
            temperature=0.1,
            max_tokens=2048,
            context_window=4096,
            verbose=False
        )
        
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        raise VectorIndexError(f"Failed to initialize LLM: {e}")

def create_service_context(embedding_model_name: str = "all-MiniLM-L6-v2", 
                          llm_model_path: Optional[str] = None) -> ServiceContext:
    """
    Create a service context for llama_index.
    
    Args:
        embedding_model_name: Name of the embedding model to use
        llm_model_path: Path to the LLaMA model (optional)
        
    Returns:
        ServiceContext object
    """
    try:
        # Initialize embedding model
        embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
        
        # Initialize LLM if model path is provided
        llm = None
        if llm_model_path and os.path.exists(llm_model_path):
            llm = initialize_llm(llm_model_path)
        
        # Create node parser
        node_parser = SimpleNodeParser.from_defaults(
            chunk_size=512,
            chunk_overlap=50
        )
        
        # Create service context
        if llm:
            service_context = ServiceContext.from_defaults(
                llm=llm,
                embed_model=embed_model,
                node_parser=node_parser
            )
        else:
            service_context = ServiceContext.from_defaults(
                embed_model=embed_model,
                node_parser=node_parser
            )
        
        return service_context
    except Exception as e:
        logger.error(f"Error creating service context: {e}")
        raise VectorIndexError(f"Failed to create service context: {e}")

def create_documents_from_resume(resume: Dict[str, Any]) -> List[Document]:
    """
    Create documents from a resume.
    
    Args:
        resume: Dictionary containing parsed resume information
        
    Returns:
        List of Document objects
    """
    try:
        # Extract information from resume
        name = resume.get("name", "")
        email = resume.get("email", "")
        phone = resume.get("phone", "")
        skills = resume.get("skills", [])
        experience = resume.get("experience", [])
        education = resume.get("education", [])
        summary = resume.get("summary", "")
        
        # Format skills
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        
        # Format experience
        experience_str = ""
        if isinstance(experience, list):
            for i, exp in enumerate(experience):
                if isinstance(exp, dict):
                    company = exp.get("company", "")
                    title = exp.get("title", "")
                    dates = exp.get("dates", "")
                    description = exp.get("description", "")
                    experience_str += f"{i+1}. {title} at {company} ({dates}): {description}\n\n"
                elif isinstance(exp, str):
                    experience_str += f"{i+1}. {exp}\n\n"
        
        # Format education
        education_str = ""
        if isinstance(education, list):
            for i, edu in enumerate(education):
                if isinstance(edu, dict):
                    institution = edu.get("institution", "")
                    degree = edu.get("degree", "")
                    dates = edu.get("dates", "")
                    education_str += f"{i+1}. {degree} from {institution} ({dates})\n\n"
                elif isinstance(edu, str):
                    education_str += f"{i+1}. {edu}\n\n"
        
        # Create documents
        documents = []
        
        # Create main resume document
        resume_text = f"""
        # Resume: {name}
        
        ## Contact Information
        - Name: {name}
        - Email: {email}
        - Phone: {phone}
        
        ## Summary
        {summary}
        
        ## Skills
        {skills_str}
        
        ## Experience
        {experience_str}
        
        ## Education
        {education_str}
        """
        
        main_doc = Document(
            text=resume_text,
            metadata={
                "source": "resume",
                "name": name,
                "document_type": "resume"
            }
        )
        documents.append(main_doc)
        
        # Create individual skill documents
        for skill in skills:
            if isinstance(skill, str):
                skill_doc = Document(
                    text=f"Skill: {skill}",
                    metadata={
                        "source": "resume",
                        "name": name,
                        "document_type": "skill"
                    }
                )
                documents.append(skill_doc)
        
        return documents
    except Exception as e:
        logger.error(f"Error creating documents from resume: {e}")
        raise VectorIndexError(f"Failed to create documents from resume: {e}")

def create_documents_from_jobs(jobs: List[Job]) -> List[Document]:
    """
    Create documents from job listings.
    
    Args:
        jobs: List of Job objects
        
    Returns:
        List of Document objects
    """
    try:
        documents = []
        
        for job in jobs:
            # Create main job document
            job_text = f"""
            # Job: {job.title} at {job.company}
            
            ## Overview
            - Title: {job.title}
            - Company: {job.company}
            - Location: {job.location}
            - Date Posted: {job.date_posted}
            - Source: {job.source}
            - URL: {job.url}
            
            ## Description
            {job.description}
            
            ## Additional Information
            - Salary: {job.salary if job.salary else "Not specified"}
            - Job Type: {job.job_type if job.job_type else "Not specified"}
            """
            
            job_doc = Document(
                text=job_text,
                metadata={
                    "source": job.source,
                    "company": job.company,
                    "title": job.title,
                    "url": job.url,
                    "document_type": "job"
                }
            )
            documents.append(job_doc)
        
        return documents
    except Exception as e:
        logger.error(f"Error creating documents from jobs: {e}")
        raise VectorIndexError(f"Failed to create documents from jobs: {e}")

def build_index(documents: List[Document], service_context: ServiceContext, 
               persist_dir: Optional[str] = None) -> VectorStoreIndex:
    """
    Build a vector index from documents.
    
    Args:
        documents: List of Document objects
        service_context: ServiceContext object
        persist_dir: Directory to persist the index (optional)
        
    Returns:
        VectorStoreIndex object
    """
    try:
        # Build index
        index = VectorStoreIndex.from_documents(
            documents,
            service_context=service_context
        )
        
        # Persist index if directory is provided
        if persist_dir:
            # Create directory if it doesn't exist
            os.makedirs(persist_dir, exist_ok=True)
            
            # Save index
            index.storage_context.persist(persist_dir=persist_dir)
            logger.info(f"Index persisted to {persist_dir}")
        
        return index
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise VectorIndexError(f"Failed to build index: {e}")

def load_index(persist_dir: str, service_context: ServiceContext) -> VectorStoreIndex:
    """
    Load a vector index from disk.
    
    Args:
        persist_dir: Directory where the index is persisted
        service_context: ServiceContext object
        
    Returns:
        VectorStoreIndex object
    """
    try:
        # Check if directory exists
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(f"Index directory not found: {persist_dir}")
        
        # Load storage context
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        
        # Load index
        index = load_index_from_storage(
            storage_context=storage_context,
            service_context=service_context
        )
        
        return index
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        raise VectorIndexError(f"Failed to load index: {e}")

def build_or_load_index(resume: Optional[Dict[str, Any]] = None, jobs: Optional[List[Job]] = None, 
                       embedding_model_name: str = "all-MiniLM-L6-v2", 
                       llm_model_path: Optional[str] = None, 
                       persist_dir: Optional[str] = "index_data") -> VectorStoreIndex:
    """
    Build or load a vector index.
    
    Args:
        resume: Dictionary containing parsed resume information (optional)
        jobs: List of Job objects (optional)
        embedding_model_name: Name of the embedding model to use
        llm_model_path: Path to the LLaMA model (optional)
        persist_dir: Directory to persist the index (optional)
        
    Returns:
        VectorStoreIndex object
    """
    try:
        # Create service context
        service_context = create_service_context(embedding_model_name, llm_model_path)
        
        # Check if index exists
        if persist_dir and os.path.exists(persist_dir):
            # Load existing index
            index = load_index(persist_dir, service_context)
            
            # Add new documents if provided
            documents = []
            
            if resume:
                resume_docs = create_documents_from_resume(resume)
                documents.extend(resume_docs)
            
            if jobs:
                job_docs = create_documents_from_jobs(jobs)
                documents.extend(job_docs)
            
            if documents:
                # Insert new documents
                for doc in documents:
                    index.insert(doc)
                
                # Persist updated index
                if persist_dir:
                    index.storage_context.persist(persist_dir=persist_dir)
                    logger.info(f"Updated index persisted to {persist_dir}")
        else:
            # Create new index
            documents = []
            
            if resume:
                resume_docs = create_documents_from_resume(resume)
                documents.extend(resume_docs)
            
            if jobs:
                job_docs = create_documents_from_jobs(jobs)
                documents.extend(job_docs)
            
            if not documents:
                raise ValueError("No documents provided to build index")
            
            # Build index
            index = build_index(documents, service_context, persist_dir)
        
        return index
    except Exception as e:
        logger.error(f"Error building or loading index: {e}")
        raise VectorIndexError(f"Failed to build or load index: {e}")

def query_index(index: VectorStoreIndex, query: str, llm_model_path: Optional[str] = None) -> str:
    """
    Query the vector index.
    
    Args:
        index: VectorStoreIndex object
        query: Query string
        llm_model_path: Path to the LLaMA model (optional)
        
    Returns:
        Query response
    """
    try:
        # Initialize LLM if model path is provided
        llm = None
        if llm_model_path and os.path.exists(llm_model_path):
            llm = initialize_llm(llm_model_path)
        
        # Create query engine
        if llm:
            query_engine = index.as_query_engine(llm=llm)
        else:
            query_engine = index.as_query_engine()
        
        # Execute query
        response = query_engine.query(query)
        
        return str(response)
    except Exception as e:
        logger.error(f"Error querying index: {e}")
        raise VectorIndexError(f"Failed to query index: {e}")

def save_resume_to_file(resume: Dict[str, Any], file_path: str) -> None:
    """
    Save resume to a file.
    
    Args:
        resume: Dictionary containing parsed resume information
        file_path: Path to save the resume
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save resume
        with open(file_path, 'w') as file:
            json.dump(resume, file, indent=2)
        
        logger.info(f"Resume saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving resume: {e}")
        raise VectorIndexError(f"Failed to save resume: {e}")

def load_resume_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load resume from a file.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dictionary containing parsed resume information
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        # Load resume
        with open(file_path, 'r') as file:
            resume = json.load(file)
        
        return resume
    except Exception as e:
        logger.error(f"Error loading resume: {e}")
        raise VectorIndexError(f"Failed to load resume: {e}")

if __name__ == "__main__":
    # Example usage
    import sys
    from jobhuntgpt.job_fetcher import Job
    
    # Create a sample resume
    resume = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "123-456-7890",
        "skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "JavaScript"],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Data Scientist",
                "dates": "2020-2023",
                "description": "Developed machine learning models for predictive analytics."
            },
            {
                "company": "Sample Inc",
                "title": "Software Engineer",
                "dates": "2018-2020",
                "description": "Built web applications using Python and JavaScript."
            }
        ],
        "education": [
            {
                "institution": "University of Example",
                "degree": "Master of Science in Computer Science",
                "dates": "2016-2018"
            }
        ],
        "summary": "Experienced data scientist and software engineer with a passion for machine learning."
    }
    
    # Create sample jobs
    jobs = [
        Job(
            title="Senior Data Scientist",
            company="Tech Corp",
            location="Remote",
            description="Looking for an experienced data scientist with Python and machine learning skills.",
            url="https://example.com/job1",
            date_posted="2023-07-01",
            source="example"
        ),
        Job(
            title="Software Engineer",
            company="Dev Inc",
            location="New York",
            description="Seeking a software engineer with JavaScript and SQL experience.",
            url="https://example.com/job2",
            date_posted="2023-07-02",
            source="example"
        )
    ]
    
    # Build index
    index = build_or_load_index(resume, jobs, persist_dir="index_data")
    
    # Query index
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "What are the best job matches for someone with Python and machine learning skills?"
    
    response = query_index(index, query)
    print(f"Query: {query}")
    print(f"Response: {response}")
