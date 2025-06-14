import pytest
from unittest.mock import Mock
from workflows.resume_processor.nodes.absolute_rating import AbsoluteRatingNode
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
        scores={
            "jd_alignment": 8.0,
            "cultural_fit": 7.5,
            "uniqueness": 7.0
        }
    )

@pytest.fixture
def absolute_rating():
    """Create an absolute rating instance"""
    return AbsoluteRatingNode()

def test_absolute_rating_initialization(absolute_rating):
    """Test absolute rating initialization"""
    assert absolute_rating is not None

def test_compute_rating_success(absolute_rating, mock_state):
    """Test successful rating computation"""
    result = absolute_rating.compute_rating(mock_state)
    
    assert result["status"] == "COMPLETED"
    assert result["message"] == "Success"
    assert "final_score" in result
    assert result["final_score"] > 0
    assert mock_state.candidate_status == "COMPLETED"

def test_compute_rating_missing_scores(absolute_rating, mock_state):
    """Test rating computation with missing scores"""
    mock_state.scores = {}
    
    result = absolute_rating.compute_rating(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Missing required scores" in result["message"]
    assert mock_state.candidate_status == "FAILED"

def test_compute_rating_missing_weights(absolute_rating, mock_state):
    """Test rating computation with missing weights"""
    mock_state.weights = {}
    
    result = absolute_rating.compute_rating(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Missing required weights" in result["message"]
    assert mock_state.candidate_status == "FAILED"

def test_calculate_weighted_score(absolute_rating, mock_state):
    """Test weighted score calculation"""
    weights = mock_state.weights
    scores = mock_state.scores
    
    weighted_score = absolute_rating._calculate_weighted_score(scores, weights)
    
    assert weighted_score > 0
    assert weighted_score <= 10.0

def test_determine_status(absolute_rating, mock_state):
    """Test status determination"""
    threshold = mock_state.thresholds["jd_threshold"]
    error_boundary = mock_state.error_boundary
    
    # Test above threshold
    status = absolute_rating._determine_status(8.0, threshold, error_boundary)
    assert status == "PASSED"
    
    # Test below threshold
    status = absolute_rating._determine_status(6.0, threshold, error_boundary)
    assert status == "FAILED"
    
    # Test boundary case
    status = absolute_rating._determine_status(7.0, threshold, error_boundary)
    assert status == "BOUNDARY" 