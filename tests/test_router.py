import pytest
from unittest.mock import Mock
from workflows.resume_processor.nodes.router import RouterNode
from workflows.resume_processor.state import ResumeProcessorState

@pytest.fixture
def mock_state():
    """Create a mock state with test data"""
    return ResumeProcessorState(
        candidate_id="test_candidate",
        s3_client=Mock(),
        dynamo_client=Mock(),
        resume_data={"content": "Test resume content"},
        jd_data={"content": "Test job description"},
        company_values={"values": ["value1", "value2"]},
        example_resume_insights_output_template={"template": "Test template"},
        past_successes_insight_document={"successes": ["success1", "success2"]},
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
        scores={"jd_alignment": 8.0}
    )

@pytest.fixture
def router():
    """Create a router instance"""
    return RouterNode()

def test_router_initialization(router):
    """Test router initialization"""
    assert router is not None

def test_route_above_threshold(router, mock_state):
    """Test routing when score is above threshold"""
    result = router.route(mock_state)
    
    assert result["status"] == "COMPLETED"
    assert result["message"] == "Success"
    assert result["next_node"] == "cultural_fit"
    assert mock_state.candidate_status == "PASSED_JD"

def test_route_below_threshold(router, mock_state):
    """Test routing when score is below threshold"""
    mock_state.scores["jd_alignment"] = 6.0
    
    result = router.route(mock_state)
    
    assert result["status"] == "COMPLETED"
    assert result["message"] == "Success"
    assert result["next_node"] == "absolute_rating"
    assert mock_state.candidate_status == "FAILED_JD"

def test_route_missing_score(router, mock_state):
    """Test routing when score is missing"""
    mock_state.scores = {}
    
    result = router.route(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Missing JD alignment score" in result["message"]
    assert mock_state.candidate_status == "FAILED"

def test_route_missing_threshold(router, mock_state):
    """Test routing when threshold is missing"""
    mock_state.thresholds = {}
    
    result = router.route(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Missing JD threshold" in result["message"]
    assert mock_state.candidate_status == "FAILED" 