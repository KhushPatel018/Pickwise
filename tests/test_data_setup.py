import os
import json
import uuid
from datetime import datetime
from utils.aws.s3_client import S3Client
from utils.aws.dynamo_client import DynamoClient

# Test data paths
TEST_DATA_DIR = "tests/test_data"
SAMPLE_RESUME_PATH = os.path.join(TEST_DATA_DIR, "sample_resume.json")
SAMPLE_JD_PATH = os.path.join(TEST_DATA_DIR, "sample_jd.json")
SAMPLE_VALUES_PATH = os.path.join(TEST_DATA_DIR, "sample_values.json")
SAMPLE_TEMPLATE_PATH = os.path.join(TEST_DATA_DIR, "sample_template.json")
SAMPLE_SUCCESSES_PATH = os.path.join(TEST_DATA_DIR, "sample_successes.json")

def create_test_files():
    """Create test data files locally"""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Sample resume data
    with open(SAMPLE_RESUME_PATH, 'w') as f:
        json.dump({
            "name": "John Doe",
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2 years",
                    "description": "Developed web applications using Python and React"
                }
            ],
            "skills": ["Python", "React", "AWS", "Docker"],
            "education": "BS Computer Science"
        }, f)
    
    # Sample job description
    with open(SAMPLE_JD_PATH, 'w') as f:
        json.dump({
            "title": "Senior Software Engineer",
            "requirements": [
                "5+ years of Python experience",
                "Strong knowledge of web frameworks",
                "Experience with cloud platforms"
            ],
            "responsibilities": [
                "Design and develop scalable applications",
                "Lead technical discussions",
                "Mentor junior developers"
            ]
        }, f)
    
    # Sample company values
    with open(SAMPLE_VALUES_PATH, 'w') as f:
        json.dump({
            "values": [
                "Innovation",
                "Collaboration",
                "Excellence",
                "Customer Focus"
            ]
        }, f)
    
    # Sample template
    with open(SAMPLE_TEMPLATE_PATH, 'w') as f:
        json.dump({
            "sections": [
                "Technical Skills",
                "Experience",
                "Education",
                "Projects"
            ]
        }, f)
    
    # Sample past successes
    with open(SAMPLE_SUCCESSES_PATH, 'w') as f:
        json.dump({
            "successful_candidates": [
                {
                    "name": "Jane Smith",
                    "role": "Software Engineer",
                    "key_qualities": [
                        "Strong problem-solving skills",
                        "Excellent communication",
                        "Team player"
                    ]
                }
            ]
        }, f)

def upload_to_s3(s3_client):
    """Upload test files to S3"""
    bucket = os.getenv("S3_BUCKET_NAME")
    test_prefix = f"test_data/{uuid.uuid4()}/"
    
    # Upload files
    files = {
        "resume.json": SAMPLE_RESUME_PATH,
        "jd.json": SAMPLE_JD_PATH,
        "values.json": SAMPLE_VALUES_PATH,
        "template.json": SAMPLE_TEMPLATE_PATH,
        "successes.json": SAMPLE_SUCCESSES_PATH
    }
    
    s3_urls = {}
    for filename, local_path in files.items():
        s3_key = f"{test_prefix}{filename}"
        with open(local_path, 'rb') as f:
            s3_client.put_object(bucket, s3_key, f.read())
        s3_urls[filename] = f"s3://{bucket}/{s3_key}"
    
    return s3_urls

def setup_dynamo_test_data(dynamo_client):
    """Create test data in DynamoDB"""
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    candidate_id = f"test_candidate_{uuid.uuid4()}"
    
    # Create test candidate record
    dynamo_client.put_item(
        table_name,
        {
            "candidate_id": candidate_id,
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "test_data": True,
                "test_run_id": str(uuid.uuid4())
            }
        }
    )
    
    return candidate_id

def setup_test_environment():
    """Set up complete test environment with S3 and DynamoDB"""
    print("Setting up test environment...")
    
    # Create test files
    create_test_files()
    print("Created test files locally")
    
    # Initialize clients
    s3_client = S3Client()
    dynamo_client = DynamoClient()
    
    # Upload to S3
    s3_urls = upload_to_s3(s3_client)
    print("Uploaded test files to S3")
    
    # Setup DynamoDB
    candidate_id = setup_dynamo_test_data(dynamo_client)
    print("Created test data in DynamoDB")
    
    return {
        "candidate_id": candidate_id,
        "s3_urls": s3_urls,
        "s3_client": s3_client,
        "dynamo_client": dynamo_client
    }

if __name__ == "__main__":
    # Run setup
    test_env = setup_test_environment()
    print("\nTest environment setup complete!")
    print(f"Candidate ID: {test_env['candidate_id']}")
    print("\nS3 URLs:")
    for filename, url in test_env["s3_urls"].items():
        print(f"{filename}: {url}") 