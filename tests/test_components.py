import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from workflows.resume_processor.nodes.jd_analysis_agent import JDAnalysisAgent
from workflows.resume_processor.nodes.router import RouterNode
from workflows.resume_processor.nodes.absolute_rating import AbsoluteRatingNode
from workflows.resume_processor.state import ResumeProcessorState
from test_data_setup import setup_test_environment

# Load environment variables
load_dotenv()

def create_test_state(test_env):
    """Create a test state with real data from S3"""
    return ResumeProcessorState(
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

def test_jd_analysis(test_env):
    """Test JD Analysis Agent with real data"""
    print("\nTesting JD Analysis Agent...")
    
    # Initialize LLM and agent
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    agent = JDAnalysisAgent(llm)
    
    # Create test state
    state = create_test_state(test_env)
    
    # Run analysis
    result = agent.analyze_resume(state)
    
    # Print results
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if result['status'] == "COMPLETED":
        print("Scores:")
        for key, value in result['scores'].items():
            print(f"  {key}: {value}")
        print("\nAnalysis Result:")
        print(json.dumps(state.analysis_result, indent=2))
        
        # Verify S3 save
        if state.analysis_result:
            print("\nAnalysis saved to S3")
        
        # Verify DynamoDB update
        dynamo_item = test_env["dynamo_client"].get_item(
            os.getenv("DYNAMODB_TABLE_NAME"),
            {"candidate_id": test_env["candidate_id"]}
        )
        print("DynamoDB Status:", dynamo_item.get("status"))

def test_router(test_env):
    """Test Router Node with real data"""
    print("\nTesting Router Node...")
    
    # Create router
    router = RouterNode()
    
    # Create test state with JD score
    state = create_test_state(test_env)
    state.scores["jd_alignment"] = 8.5  # Above threshold
    
    # Test routing
    result = router.route(state)
    
    # Print results
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Next Node: {result['next_node']}")
    print(f"Candidate Status: {state.candidate_status}")
    
    # Verify DynamoDB update
    dynamo_item = test_env["dynamo_client"].get_item(
        os.getenv("DYNAMODB_TABLE_NAME"),
        {"candidate_id": test_env["candidate_id"]}
    )
    print("DynamoDB Status:", dynamo_item.get("status"))
    
    # Test with below threshold score
    state.scores["jd_alignment"] = 6.5  # Below threshold
    result = router.route(state)
    print("\nBelow threshold test:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Next Node: {result['next_node']}")
    print(f"Candidate Status: {state.candidate_status}")
    
    # Verify DynamoDB update
    dynamo_item = test_env["dynamo_client"].get_item(
        os.getenv("DYNAMODB_TABLE_NAME"),
        {"candidate_id": test_env["candidate_id"]}
    )
    print("DynamoDB Status:", dynamo_item.get("status"))

def test_absolute_rating(test_env):
    """Test Absolute Rating Node with real data"""
    print("\nTesting Absolute Rating Node...")
    
    # Create rating node
    rating_node = AbsoluteRatingNode()
    
    # Create test state with scores
    state = create_test_state(test_env)
    state.scores = {
        "jd_alignment": 8.5,
        "cultural_fit": 7.8,
        "uniqueness": 8.2
    }
    
    # Test rating
    result = rating_node.compute_rating(state)
    
    # Print results
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if result['status'] == "COMPLETED":
        print("Scores:")
        for key, value in result['scores'].items():
            print(f"  {key}: {value}")
        print(f"Candidate Status: {state.candidate_status}")
        
        # Verify DynamoDB update
        dynamo_item = test_env["dynamo_client"].get_item(
            os.getenv("DYNAMODB_TABLE_NAME"),
            {"candidate_id": test_env["candidate_id"]}
        )
        print("DynamoDB Status:", dynamo_item.get("status"))

if __name__ == "__main__":
    # Setup test environment
    print("Setting up test environment...")
    test_env = setup_test_environment()
    
    # Run all component tests
    test_jd_analysis(test_env)
    test_router(test_env)
    test_absolute_rating(test_env)
    print("\nAll component tests completed!") 