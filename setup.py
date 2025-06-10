from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gai_final_project",
    version="1.0.0",
    author="GAI Final Project Team",
    author_email="team@gai-project.dev",
    description="Multi-Agent Python Developer Recruitment Assistant - GAI Final Project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zivisaiah/gai_final_project",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.7.1",
        ],
    },
) 