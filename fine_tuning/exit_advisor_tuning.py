import os
import time
from pathlib import Path
from openai import OpenAI
from openai.types.fine_tuning import FineTuningJob
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def run_fine_tuning(training_file: str, model_name: str = "gpt-3.5-turbo") -> str:
    """
    Run fine-tuning process using the new OpenAI API.
    
    Args:
        training_file: Path to the JSONL training file
        model_name: Base model to fine-tune (default: gpt-3.5-turbo)
    
    Returns:
        str: The fine-tuning job ID
    """
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables")
    
    client = OpenAI(api_key=api_key)
    
    print(f"Uploading training file: {training_file}")
    try:
        # Upload file using new API
        with open(training_file, "rb") as f:
            file_response = client.files.create(
                file=f,
                purpose="fine-tune"
            )
        file_id = file_response.id
        print(f"File uploaded successfully. File ID: {file_id}")

        # Start fine-tuning job
        print("Starting fine-tuning job...")
        job = client.fine_tuning.jobs.create(
            training_file=file_id,
            model=model_name,
            suffix="exit-advisor"
        )
        job_id = job.id
        print(f"Fine-tuning job started. Job ID: {job_id}")

        # Monitor job status
        while True:
            job_status = client.fine_tuning.jobs.retrieve(job_id)
            status = job_status.status
            
            if status == "succeeded":
                print(f"Fine-tuning completed successfully! Model: {job_status.fine_tuned_model}")
                break
            elif status in ["failed", "cancelled"]:
                print(f"Fine-tuning {status}. Error: {job_status.error if hasattr(job_status, 'error') else 'No error details'}")
                break
            else:
                print(f"Current status: {status}. Waiting...")
                time.sleep(60)  # Check every minute

        return job_id

    except Exception as e:
        print(f"Error during fine-tuning process: {str(e)}")
        raise

if __name__ == "__main__":
    data_dir = Path(__file__).parent / "data"
    training_file = data_dir / "exit_advisor_finetune.jsonl"
    
    if not training_file.exists():
        raise FileNotFoundError(f"Training file not found at: {training_file}")
        
    try:
        job_id = run_fine_tuning(str(training_file))
        print(f"\nFine-tuning completed. Job ID: {job_id}")
        print("You can monitor the job status in the OpenAI dashboard.")
    except Exception as e:
        print(f"Failed to run fine-tuning: {str(e)}")
        exit(1) 