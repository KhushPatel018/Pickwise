from pydantic import BaseModel
 
class WorkflowRequest(BaseModel):
    candidate_id: str
    resume_s3_url: str
    jd_s3_url: str
    core_values_s3_url: str
    uniqueness_description_s3_url: str
    custom_criteria_s3_url: str
    weights: dict
    jd_threshold: float
    absolute_grading_error_boundary: float
    absolute_grading_threshold: float