SCORING_RUBRIC = {
    "Required Skills Match": 35,
    "Preferred Skills Match": 20,
    "Experience Match": 20,
    "Education Match": 10,
    "Resume Quality & Strengths": 15
}

JD_OUTPUT_FORMAT = {
    "Raw Score (out of 100)": "<integer>",
    "Normalized Score (out of 10)": "<float rounded to 1 decimal place>",
    "Score Breakdown": {
        "Required Skills Match": "<score>/45",
        "Preferred Skills Match": "<score>/20",
        "Experience Match": "<score>/20",
        "Education Match": "<score>/10",
        "Resume Quality & Strengths": "<score>/5"
    },
    "Detailed Scoring": {
        "Required Skills Match": [
            {
                "skill": "<Skill Name>",
                "score_awarded": "<int>",
                "max_score": "<int>",
                "comment": "<explanation with evidence>"
            }
        ],
        "Preferred Skills Match": [
            {
                "skill": "<Skill Name>",
                "score_awarded": "<int>",
                "max_score": "<int>",
                "comment": "<explanation with evidence>"
            }
        ],
        "Experience Match": [
            {
                "criteria": "Years of Experience",
                "required": "<years>",
                "actual": "<years>",
                "score_awarded": "<int>",
                "max_score": "<int>",
                "comment": "<explanation>"
            }
        ],
        "Education Match": [
            {
                "criteria": "Degree",
                "required": "<degree>",
                "actual": "<degree>",
                "score_awarded": "<int>",
                "max_score": "<int>",
                "comment": "<explanation>"
            }
        ],
        "Resume Quality & Strengths": [
            {
                "criteria": "<sub-criteria>",
                "score_awarded": "<int>",
                "max_score": "<int>",
                "comment": "<explanation>"
            }
        ]
    },
    "Key Strengths": [
        "Bullet 1",
        "Bullet 2",
        "Bullet 3"
    ],
    "Areas for Improvement": [
        "Suggestion 1",
        "Suggestion 2",
        "Suggestion 3"
    ],
    "Verdict": "<true or false>"
} 