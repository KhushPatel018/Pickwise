"""
Constants for the resume processor workflow.
"""

# Default weights for absolute rating computation (out of 10)
DEFAULT_ABSOLUTE_RATING_WEIGHTS = {
    "jd_score_weight": 4.0,        # Job description match weight
    "cultural_fit_score_weight": 2.0,  # Cultural fit weight
    "uniqueness_score_weight": 3.0,    # Uniqueness weight
    "custom_criteria_score_weight": {  # Custom criteria weights
        "custom_criteria_1": 0.5,
        "custom_criteria_2": 0.3,
        "custom_criteria_3": 0.2
    }
}

# Default threshold for absolute rating decisions
DEFAULT_ABSOLUTE_RATING_THRESHOLD = 70.0  # 70% threshold

# Default error boundary for absolute rating decisions
DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY = 10.0  # 10% boundary 