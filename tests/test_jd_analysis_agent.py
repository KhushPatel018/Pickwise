import pytest
from unittest.mock import Mock, patch
from workflows.resume_processor.nodes.jd_analysis_agent import JDAnalysisAgent
from workflows.resume_processor.state import ResumeProcessorState

@pytest.fixture
def mock_llm():
    """Create a mock LLM instance"""
    llm = Mock()
    llm.invoke.return_value = {
        "content": "Test analysis result",
        "scores": {"jd_alignment": 8.0}
    }
    return llm

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
def agent(mock_llm):
    """Create an agent instance with mock LLM"""
    return JDAnalysisAgent(mock_llm)

def test_agent_initialization(agent, mock_llm):
    """Test agent initialization"""
    assert agent.llm == mock_llm
    assert agent.prompt_template is not None

def test_analyze_resume_success(agent, mock_state, mock_llm):
    """Test successful resume analysis"""
    result = agent.analyze_resume(mock_state)
    
    assert result["status"] == "COMPLETED"
    assert result["message"] == "Success"
    assert result["scores"]["jd_alignment"] == 8.0
    mock_llm.invoke.assert_called_once()

def test_analyze_resume_failure(agent, mock_state, mock_llm):
    """Test resume analysis failure"""
    mock_llm.invoke.side_effect = Exception("Test error")
    
    result = agent.analyze_resume(mock_state)
    
    assert result["status"] == "FAILED"
    assert "Test error" in result["message"]
    mock_llm.invoke.assert_called_once()

def test_parse_analysis_result(agent):
    """Test parsing of analysis result"""
    test_result = {
        "content": "Test analysis",
        "scores": {"jd_alignment": 8.0}
    }
    
    parsed_result = agent._parse_analysis_result(test_result)
    
    assert parsed_result["status"] == "COMPLETED"
    assert parsed_result["message"] == "Success"
    assert parsed_result["scores"]["jd_alignment"] == 8.0

def test_parse_analysis_result_invalid(agent):
    """Test parsing of invalid analysis result"""
    test_result = "Invalid result"
    
    parsed_result = agent._parse_analysis_result(test_result)
    
    assert parsed_result["status"] == "FAILED"
    assert "Invalid analysis result format" in parsed_result["message"] 