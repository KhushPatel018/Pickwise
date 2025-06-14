import pytest
from unittest.mock import Mock, patch
from workflows.resume_processor.workflow import ResumeProcessorWorkflow
from workflows.resume_processor.state import ResumeProcessorState

@pytest.fixture
def mock_llm():
    """Create a mock LLM instance"""
    return Mock()

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
        scores={}
    )

@pytest.fixture
def workflow(mock_llm):
    """Create a workflow instance with mock LLM"""
    return ResumeProcessorWorkflow(mock_llm)

def test_workflow_initialization(workflow, mock_llm):
    """Test workflow initialization"""
    assert workflow.llm == mock_llm
    assert workflow.graph is not None
    assert workflow.compiled_graph is not None

def test_process_resume_success(workflow, mock_state):
    """Test successful resume processing"""
    # Mock the graph execution
    workflow.compiled_graph = Mock()
    workflow.compiled_graph.invoke.return_value = {
        "status": "COMPLETED",
        "message": "Success",
        "scores": {"jd_alignment": 8.0}
    }

    result = workflow.process_resume(mock_state)
    
    assert result["status"] == "COMPLETED"
    assert result["message"] == "Success"
    assert result["scores"]["jd_alignment"] == 8.0
    workflow.compiled_graph.invoke.assert_called_once_with(mock_state)

def test_process_resume_failure(workflow, mock_state):
    """Test resume processing failure"""
    # Mock the graph execution to raise an exception
    workflow.compiled_graph = Mock()
    workflow.compiled_graph.invoke.side_effect = Exception("Test error")

    result = workflow.process_resume(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Test error" in result["message"]
    workflow.compiled_graph.invoke.assert_called_once_with(mock_state) 