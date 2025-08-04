"""
Basic tests for the Enterprise Recruitment Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

# Test data models
def test_candidate_profile_creation():
    """Test that we can create a candidate profile"""
    from enterprise_recruitment_agent.models import CandidateProfile
    
    candidate = CandidateProfile(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone="123-456-7890",
        skills=["Python", "React"],
        experience_years=5,
        location="San Francisco",
        education="Bachelor's in Computer Science"
    )
    
    assert candidate.name == "John Doe"
    assert candidate.experience_years == 5
    assert "Python" in candidate.skills

def test_job_posting_creation():
    """Test that we can create a job posting"""
    from enterprise_recruitment_agent.models import JobPosting
    
    job = JobPosting(
        id=1,
        title="Senior Python Developer",
        company="Tech Corp",
        location="San Francisco",
        description="We are looking for a senior Python developer...",
        requirements=["Python", "Django", "5+ years experience"],
        salary_min=120000,
        salary_max=180000,
        remote_ok=True
    )
    
    assert job.title == "Senior Python Developer"
    assert job.remote_ok is True
    assert "Python" in job.requirements

# Test resume parser
@pytest.mark.asyncio
async def test_resume_parser_initialization():
    """Test that resume parser can be initialized"""
    from enterprise_recruitment_agent.resume_parser import ResumeParser
    
    parser = ResumeParser()
    assert parser is not None

# Test matching engine
@pytest.mark.asyncio
async def test_matching_engine_initialization():
    """Test that matching engine can be initialized"""
    from enterprise_recruitment_agent.matching_engine import MatchingEngine
    
    engine = MatchingEngine()
    assert engine is not None

# Test bulk processor
@pytest.mark.asyncio
async def test_bulk_processor_initialization():
    """Test that bulk processor can be initialized"""
    from enterprise_recruitment_agent.bulk_processor import BulkProcessor
    from enterprise_recruitment_agent.database import DatabaseManager
    from enterprise_recruitment_agent.resume_parser import ResumeParser
    
    # Create real instances
    db_manager = DatabaseManager()
    resume_parser = ResumeParser()
    
    processor = BulkProcessor(db_manager, resume_parser)
    assert processor is not None

# Test analytics engine
@pytest.mark.asyncio
async def test_analytics_engine_initialization():
    """Test that analytics engine can be initialized"""
    from enterprise_recruitment_agent.analytics import AnalyticsEngine
    from enterprise_recruitment_agent.database import DatabaseManager
    
    # Create real instance
    db_manager = DatabaseManager()
    engine = AnalyticsEngine(db_manager)
    assert engine is not None

# Test workflow automation
@pytest.mark.asyncio
async def test_workflow_automation_initialization():
    """Test that workflow automation can be initialized"""
    from enterprise_recruitment_agent.automation import WorkflowAutomation
    from enterprise_recruitment_agent.database import DatabaseManager
    
    # Create real instance
    db_manager = DatabaseManager()
    automation = WorkflowAutomation(db_manager)
    assert automation is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
