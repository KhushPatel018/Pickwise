import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from workflows.resume_processor.workflow import ResumeProcessorWorkflow
from workflows.resume_processor.state import ResumeProcessorState
from test_data_setup import setup_test_environment

# Load environment variables
load_dotenv()

def test_complete_workflow():
    """Test the complete workflow with real data and infrastructure"""
    print("\nSetting up test environment...")
    test_env = setup_test_environment()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create workflow
    workflow = ResumeProcessorWorkflow(llm)
    
    # Create test state with real S3 URLs
    state = ResumeProcessorState(
        candidate_id=test_env["candidate_id"],
        s3_client=test_env["s3_client"],
        dynamo_client=test_env["dynamo_client"],
        resume_data=test_env["s3_client"].get_object(
            test_env["s3_urls"]["resume.json"]
        ),
        jd_data=test_env["s3_client"].get_object(
            test_env["s3_urls"]["jd.json"]
        ),
        company_values=test_env["s3_client"].get_object(
            test_env["s3_urls"]["values.json"]
        ),
        example_resume_insights_output_template=test_env["s3_client"].get_object(
            test_env["s3_urls"]["template.json"]
        ),
        past_successes_insight_document=test_env["s3_client"].get_object(
            test_env["s3_urls"]["successes.json"]
        ),
        weights={
            "jd_alignment": 0.5,
            "cultural_fit": 0.3,
            "uniqueness": 0.2
        },
        thresholds={
            "jd_threshold": 7.0,
            "cultural_fit_threshold": 6.0,
            "uniqueness_threshold": 6.0
        },
        error_boundary=0.5,
        scores={}
    )
    
    print("\nRunning workflow...")
    result = workflow.process_resume(state)
    
    # Print results
    print("\nWorkflow Results:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result["status"] == "COMPLETED":
        print("\nScores:")
        for key, value in result["scores"].items():
            print(f"  {key}: {value}")
        
        print("\nCandidate Status:", state.candidate_status)
        
        # Verify DynamoDB update
        dynamo_item = test_env["dynamo_client"].get_item(
            os.getenv("DYNAMODB_TABLE_NAME"),
            {"candidate_id": test_env["candidate_id"]}
        )
        print("\nDynamoDB Status:", dynamo_item.get("status"))
        
        # Verify S3 analysis result
        if state.analysis_result:
            print("\nAnalysis Result saved to S3")
    
    return result

if __name__ == "__main__":
    # Run the test
    result = test_complete_workflow()
    print("\nIntegration test completed!") 