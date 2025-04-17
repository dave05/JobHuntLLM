# JobHuntGPT

An LLM-powered job search assistant that helps you find, apply for, and track job opportunities.

[![JobHuntGPT CI/CD](https://github.com/dave05/JobHuntLLM/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/dave05/JobHuntLLM/actions/workflows/ci-cd.yml)

## Features

- **Resume Parsing**: Extract skills, experience, and education from your resume
- **Job Fetching**: Fetch job listings from multiple sources (LinkedIn, Indeed, CSV, JSON)
- **Job Matching**: Match and rank job listings against your resume
- **Email Composition**: Generate tailored cover letters and follow-up emails
- **Scheduling**: Schedule reminders and follow-ups for job applications
- **Vector Search**: Semantic search across your resume and job listings
- **Web Interface**: User-friendly web interface for managing your job search
- **API Endpoints**: RESTful API for integration with other applications

## Installation

### Prerequisites

- Python 3.10+
- [LLaMA model](https://github.com/ggerganov/llama.cpp) (optional, for enhanced text generation)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/jobhuntgpt.git
cd jobhuntgpt
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:

```bash
pip install -e .
```

4. Create a configuration file:

```bash
cp config.yaml.template config.yaml
```

5. Edit the configuration file to set your preferences and API keys.

## Usage

JobHuntGPT provides a command-line interface with several commands:

### Parse Resume

```bash
jobhuntgpt parse --resume path/to/your/resume.pdf --output resume.json
```

### Fetch Jobs

```bash
# From CSV file
jobhuntgpt fetch --source csv --query path/to/jobs.csv

# From LinkedIn
jobhuntgpt fetch --source linkedin --query "software engineer" --location "remote" --limit 20
```

### Rank Jobs

```bash
jobhuntgpt rank --resume resume.json --jobs jobs.json --top 10
```

### Compose Cover Letter

```bash
jobhuntgpt compose --resume resume.json --job job.json --type cover
```

### Schedule Follow-up

```bash
jobhuntgpt schedule --job job.json --days 7
```

### Run Complete Workflow

```bash
jobhuntgpt run-all --resume path/to/your/resume.pdf --source linkedin --query "software engineer" --location "remote" --top 5
```

## Configuration

The `config.yaml` file allows you to configure various aspects of JobHuntGPT:

```yaml
# API Keys
api_keys:
  google_calendar: "YOUR_GOOGLE_CALENDAR_API_KEY"
  linkedin: "YOUR_LINKEDIN_API_KEY"
  indeed: "YOUR_INDEED_API_KEY"

# LLM Configuration
llm:
  model_path: "path/to/llama-2-7b.gguf"  # Path to your LLaMA model
  n_ctx: 2048  # Context window size
  n_gpu_layers: -1  # Number of layers to offload to GPU (-1 for all)
  temperature: 0.7
  max_tokens: 1024

# Job Search Configuration
job_search:
  default_query: "software engineer"
  default_location: "remote"
  max_jobs: 100
  sources:
    - linkedin
    - indeed
    - csv

# Resume Configuration
resume:
  path: "path/to/your/resume.pdf"

# Scheduler Configuration
scheduler:
  follow_up_days: 7  # Days after application to follow up
  reminder_days: 1  # Days before interview to remind
```

## Docker

You can run JobHuntGPT using Docker Compose:

```bash
# Start the application
docker-compose up -d

# Access the web interface at http://localhost
# API endpoints are available at http://localhost/api
```

Or you can run just the CLI using Docker:

```bash
# Build the Docker image
docker build -t jobhuntgpt .

# Run JobHuntGPT
docker run -v $(pwd):/app/data jobhuntgpt run-all --resume /app/data/resume.pdf --source csv --query /app/data/jobs.csv
```

## Development

### GitHub Codespaces

This repository is configured for GitHub Codespaces. To start developing:

1. Click the "Code" button on the repository page
2. Select the "Codespaces" tab
3. Click "Create codespace on main"

This will create a development environment with all dependencies installed.

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black jobhuntgpt tests
```

### Linting

```bash
flake8 jobhuntgpt tests
```

### API Documentation

When running the application, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [LangChain](https://github.com/hwchase17/langchain) for the agent framework
- [LLaMA](https://github.com/facebookresearch/llama) for the language model
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) for embeddings
- [LlamaIndex](https://github.com/jerryjliu/llama_index) for vector indexing
