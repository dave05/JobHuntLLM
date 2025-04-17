"""Setup script for JobHuntGPT."""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="jobhuntgpt",
    version="0.1.0",
    description="An LLM-powered job search assistant",
    author="JobHuntGPT Team",
    author_email="example@example.com",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "jobhuntgpt=jobhuntgpt.cli:app",
        ],
    },
    python_requires=">=3.10",
)
