"""
Data models for the Enterprise Recruitment Agent
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum


class ApplicationStatus(Enum):
    """Application status enumeration"""
    APPLIED = "applied"
    SCREENING = "screening" 
    PHONE_SCREEN = "phone_screen"
    TECHNICAL_INTERVIEW = "technical_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER_PENDING = "offer_pending"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InterviewType(Enum):
    """Interview type enumeration"""
    PHONE_SCREEN = "phone_screen"
    VIDEO_CALL = "video_call"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    ONSITE = "onsite"
    FINAL = "final"


@dataclass
class CandidateProfile:
    """Comprehensive candidate profile"""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: Optional[str] = None
    location: Optional[str] = None
    
    # Professional Information
    current_position: Optional[str] = None
    experience_years: int = 0
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    
    # Education
    education: List[Dict[str, Any]] = field(default_factory=list)
    education_level: Optional[str] = None
    
    # Resume and Portfolio
    resume_text: str = ""
    resume_file_path: Optional[str] = None
    portfolio_links: List[str] = field(default_factory=list)
    
    # Preferences
    salary_expectation: Optional[int] = None
    preferred_locations: List[str] = field(default_factory=list)
    remote_preference: bool = False
    availability_date: Optional[date] = None
    
    # Metadata
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Scoring
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None


@dataclass
class JobPosting:
    """Comprehensive job posting"""
    id: Optional[int] = None
    title: str = ""
    company: str = ""
    department: Optional[str] = None
    
    # Job Details
    description: str = ""
    responsibilities: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    
    # Skills and Experience
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_min: int = 0
    experience_max: int = 10
    
    # Education and Certifications
    education_requirements: Optional[str] = None
    certifications: List[str] = field(default_factory=list)
    
    # Compensation and Benefits
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    benefits: List[str] = field(default_factory=list)
    
    # Location and Work Style
    location: Optional[str] = None
    remote_ok: bool = False
    hybrid_ok: bool = False
    travel_required: Optional[str] = None
    
    # Job Metadata
    job_type: str = "Full-time"  # Full-time, Part-time, Contract, Internship
    employment_type: str = "Permanent"  # Permanent, Contract, Temporary
    industry: Optional[str] = None
    seniority_level: Optional[str] = None
    
    # Application Details
    application_deadline: Optional[date] = None
    start_date: Optional[date] = None
    urgency: str = "Normal"  # Low, Normal, High, Urgent
    
    # Status and Tracking
    status: str = "Open"  # Open, Paused, Closed, Filled
    posted_date: Optional[date] = None
    filled_date: Optional[date] = None
    hiring_manager: Optional[str] = None
    recruiter: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MatchResult:
    """Candidate-job matching result"""
    candidate_id: int
    job_id: int
    candidate_name: str
    job_title: str
    
    # Scoring
    overall_match_score: float
    skill_match_score: float
    experience_match_score: float
    location_match_score: float
    education_match_score: float
    salary_match_score: float
    
    # Detailed Analysis
    matching_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    skill_gap_percentage: float = 0.0
    
    # Experience Analysis
    experience_fit: str = ""  # "Perfect", "Over-qualified", "Under-qualified"
    experience_gap_years: int = 0
    
    # Other Factors
    location_compatibility: bool = True
    salary_compatibility: bool = True
    availability_match: bool = True
    
    # Recommendation
    recommendation: str = ""  # "Strong Match", "Good Match", "Potential Match", "Poor Match"
    match_reasons: List[str] = field(default_factory=list)
    concern_areas: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None


@dataclass
class InterviewSchedule:
    """Interview scheduling information"""
    application_id: int
    candidate_id: int
    job_id: int
    interview_type: InterviewType
    scheduled_date: datetime
    
    # Optional fields with defaults
    id: Optional[int] = None
    duration_minutes: int = 60
    interviewer: str = ""
    interview_panel: List[str] = field(default_factory=list)
    
    # Location/Method
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Preparation
    preparation_materials: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    
    # Status and Feedback
    status: str = "Scheduled"  # Scheduled, Completed, Cancelled, No-show
    feedback: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale
    recommendation: Optional[str] = None
    
    # Follow-up
    next_steps: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Application:
    """Job application tracking"""
    candidate_id: int
    job_id: int
    
    # Optional fields with defaults
    id: Optional[int] = None
    application_date: Optional[datetime] = None
    status: ApplicationStatus = ApplicationStatus.APPLIED
    source: Optional[str] = None
    
    # Documents
    cover_letter: Optional[str] = None
    additional_documents: List[str] = field(default_factory=list)
    
    # Scoring and Assessment
    initial_score: Optional[float] = None
    screening_score: Optional[float] = None
    interview_scores: Dict[str, float] = field(default_factory=dict)
    final_score: Optional[float] = None
    
    # Process Tracking
    screening_completed: bool = False
    interviews_completed: int = 0
    references_checked: bool = False
    background_check_completed: bool = False
    
    # Decision Making
    recommendation: Optional[str] = None
    decision: Optional[str] = None
    decision_date: Optional[datetime] = None
    decision_maker: Optional[str] = None
    
    # Communication
    last_contact_date: Optional[datetime] = None
    next_action: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ScreeningCriteria:
    """Automated screening criteria"""
    job_id: int
    
    # Experience Requirements
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    
    # Skills Requirements
    required_skills: List[str] = field(default_factory=list)
    required_skill_count: Optional[int] = None
    skill_match_threshold: float = 0.7
    
    # Education Requirements
    min_education_level: Optional[str] = None
    required_degrees: List[str] = field(default_factory=list)
    required_certifications: List[str] = field(default_factory=list)
    
    # Location and Availability
    location_required: bool = False
    remote_acceptable: bool = True
    availability_required: Optional[date] = None
    
    # Salary Expectations
    max_salary_expectation: Optional[int] = None
    salary_negotiable: bool = True
    
    # Scoring Thresholds
    min_overall_score: float = 0.6
    auto_reject_threshold: float = 0.3
    auto_advance_threshold: float = 0.8
    
    # Custom Criteria
    custom_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Analytics:
    """Analytics and reporting data structures"""
    
    @dataclass
    class JobMetrics:
        job_id: int
        total_applications: int
        qualified_candidates: int
        interviews_scheduled: int
        offers_made: int
        hires: int
        avg_time_to_hire: float
        conversion_rate: float
        quality_score: float
    
    @dataclass
    class CandidateMetrics:
        candidate_id: int
        applications_sent: int
        interviews_received: int
        offers_received: int
        response_rate: float
        avg_application_score: float
    
    @dataclass
    class SourceMetrics:
        source_name: str
        candidate_count: int
        application_count: int
        hire_count: int
        quality_score: float
        cost_per_hire: Optional[float] = None
    
    @dataclass
    class SkillDemand:
        skill_name: str
        job_count: int
        candidate_count: int
        demand_supply_ratio: float
        avg_salary: Optional[float] = None
