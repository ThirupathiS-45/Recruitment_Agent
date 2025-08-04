"""
Integration test for the Enterprise Recruitment Agent
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server can be initialized"""
    from enterprise_recruitment_agent.server import EnterpriseRecruitmentAgent
    
    # Mock the database connection to avoid needing a real database
    with patch('enterprise_recruitment_agent.database.DatabaseManager') as mock_db_class:
        mock_db = AsyncMock()
        mock_db_class.return_value = mock_db
        
        server = EnterpriseRecruitmentAgent()
        assert server is not None
        assert hasattr(server, 'db_manager')
        assert hasattr(server, 'resume_parser')
        assert hasattr(server, 'matching_engine')

@pytest.mark.asyncio
async def test_candidate_profile_with_job_posting():
    """Test creating a candidate and job posting together"""
    from enterprise_recruitment_agent.models import CandidateProfile, JobPosting, MatchResult
    
    # Create a candidate
    candidate = CandidateProfile(
        name="Jane Smith",
        email="jane@example.com",
        skills=["Python", "React", "PostgreSQL"],
        experience_years=3,
        location="New York"
    )
    
    # Create a job posting
    job = JobPosting(
        title="Full Stack Developer",
        company="Tech Startup",
        required_skills=["Python", "React", "JavaScript"],
        experience_min=2,
        experience_max=5,
        location="New York",
        remote_ok=True
    )
    
    # Test that both objects are created successfully
    assert candidate.name == "Jane Smith"
    assert "Python" in candidate.skills
    assert job.title == "Full Stack Developer"
    assert "Python" in job.required_skills
    
    # Test match result creation
    match_result = MatchResult(
        candidate_id=1,
        job_id=1,
        candidate_name="Jane Smith",
        job_title="Full Stack Developer",
        overall_match_score=0.85,
        skill_match_score=0.90,
        experience_match_score=0.80,
        location_match_score=1.0,
        education_match_score=0.75,
        salary_match_score=0.85,
        matching_skills=["Python", "React"],
        missing_skills=["JavaScript"],
        experience_fit="Perfect"
    )
    
    assert match_result.overall_match_score == 0.85
    assert match_result.experience_fit == "Perfect"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
