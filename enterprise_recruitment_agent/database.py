"""
Database management for the Enterprise Recruitment Agent
Handles PostgreSQL database operations with optimizations for large datasets
"""

import asyncio
import asyncpg
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict
from dotenv import load_dotenv

from models import (
    CandidateProfile, 
    JobPosting, 
    Application, 
    MatchResult, 
    InterviewSchedule,
    ApplicationStatus,
    ScreeningCriteria
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Optimized database manager for large-scale recruitment operations"""
    
    def __init__(self):
        # Load environment variables from parent directory
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        
        self.pool: Optional[asyncpg.Pool] = None
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'recruitment_db'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'techy@123'),
            'min_size': 10,  # Minimum connections for high performance
            'max_size': 50,  # Maximum connections for scalability
            'command_timeout': 60
        }
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def create_candidate(self, candidate: CandidateProfile) -> int:
        """Create a new candidate record"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO candidates (
                    name, email, phone, location, current_position, experience_years,
                    skills, certifications, languages, education, education_level,
                    resume_text, resume_file_path, portfolio_links, salary_expectation,
                    preferred_locations, remote_preference, availability_date, source,
                    overall_score, technical_score, communication_score
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22
                ) RETURNING id
            """
            
            candidate_id = await conn.fetchval(
                query,
                candidate.name, candidate.email, candidate.phone, candidate.location,
                candidate.current_position, candidate.experience_years,
                json.dumps(candidate.skills), json.dumps(candidate.certifications),
                json.dumps(candidate.languages), json.dumps(candidate.education),
                candidate.education_level, candidate.resume_text, candidate.resume_file_path,
                json.dumps(candidate.portfolio_links), candidate.salary_expectation,
                json.dumps(candidate.preferred_locations), candidate.remote_preference,
                candidate.availability_date, candidate.source, candidate.overall_score,
                candidate.technical_score, candidate.communication_score
            )
            
            logger.info(f"Created candidate {candidate.name} with ID {candidate_id}")
            return candidate_id
    
    async def create_candidates_bulk(self, candidates: List[CandidateProfile]) -> List[int]:
        """Create multiple candidates in bulk for performance"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO candidates (
                    name, email, phone, location, current_position, experience_years,
                    skills, certifications, languages, education, education_level,
                    resume_text, resume_file_path, portfolio_links, salary_expectation,
                    preferred_locations, remote_preference, availability_date, source,
                    overall_score, technical_score, communication_score
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22
                ) RETURNING id
            """
            
            candidate_ids = []
            
            # Use transaction for atomic bulk insert
            async with conn.transaction():
                for candidate in candidates:
                    candidate_id = await conn.fetchval(
                        query,
                        candidate.name, candidate.email, candidate.phone, candidate.location,
                        candidate.current_position, candidate.experience_years,
                        json.dumps(candidate.skills), json.dumps(candidate.certifications),
                        json.dumps(candidate.languages), json.dumps(candidate.education),
                        candidate.education_level, candidate.resume_text, candidate.resume_file_path,
                        json.dumps(candidate.portfolio_links), candidate.salary_expectation,
                        json.dumps(candidate.preferred_locations), candidate.remote_preference,
                        candidate.availability_date, candidate.source, candidate.overall_score,
                        candidate.technical_score, candidate.communication_score
                    )
                    candidate_ids.append(candidate_id)
            
            logger.info(f"Created {len(candidate_ids)} candidates in bulk")
            return candidate_ids
    
    async def create_job_posting(self, job: JobPosting) -> int:
        """Create a new job posting"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO job_postings (
                    title, company, department, description, responsibilities, requirements,
                    required_skills, preferred_skills, experience_min, experience_max,
                    education_requirements, certifications, salary_min, salary_max, benefits,
                    location, remote_ok, hybrid_ok, travel_required, job_type, employment_type,
                    industry, seniority_level, application_deadline, start_date, urgency,
                    status, hiring_manager, recruiter
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29
                ) RETURNING id
            """
            
            job_id = await conn.fetchval(
                query,
                job.title, job.company, job.department, job.description,
                json.dumps(job.responsibilities), json.dumps(job.requirements),
                json.dumps(job.required_skills), json.dumps(job.preferred_skills),
                job.experience_min, job.experience_max, job.education_requirements,
                json.dumps(job.certifications), job.salary_min, job.salary_max,
                json.dumps(job.benefits), job.location, job.remote_ok, job.hybrid_ok,
                job.travel_required, job.job_type, job.employment_type, job.industry,
                job.seniority_level, job.application_deadline, job.start_date,
                job.urgency, job.status, job.hiring_manager, job.recruiter
            )
            
            logger.info(f"Created job posting '{job.title}' with ID {job_id}")
            return job_id
    
    async def get_candidates_for_matching(
        self, 
        job_id: int, 
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Get candidates for job matching with optional filters"""
        async with self.get_connection() as conn:
            base_query = """
                SELECT 
                    id, name, email, experience_years, skills, location,
                    education_level, salary_expectation, remote_preference,
                    overall_score, technical_score, availability_date
                FROM candidates
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            # Apply filters
            if filters:
                if filters.get('experience_min'):
                    param_count += 1
                    base_query += f" AND experience_years >= ${param_count}"
                    params.append(filters['experience_min'])
                
                if filters.get('location') and not filters.get('remote_ok', True):
                    param_count += 1
                    base_query += f" AND location ILIKE ${param_count}"
                    params.append(f"%{filters['location']}%")
                
                if filters.get('salary_max'):
                    param_count += 1
                    base_query += f" AND (salary_expectation IS NULL OR salary_expectation <= ${param_count})"
                    params.append(filters['salary_max'])
            
            # Exclude candidates who already applied to this job
            param_count += 1
            base_query += f"""
                AND id NOT IN (
                    SELECT candidate_id FROM applications WHERE job_id = ${param_count}
                )
                ORDER BY overall_score DESC NULLS LAST
                LIMIT 1000
            """
            params.append(job_id)
            
            rows = await conn.fetch(base_query, *params)
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                candidate['skills'] = json.loads(candidate['skills'] or '[]')
                candidates.append(candidate)
            
            return candidates
    
    async def save_match_results(self, matches: List[MatchResult]) -> None:
        """Save candidate-job match results"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO match_results (
                    candidate_id, job_id, overall_match_score, skill_match_score,
                    experience_match_score, location_match_score, education_match_score,
                    salary_match_score, matching_skills, missing_skills, skill_gap_percentage,
                    experience_fit, experience_gap_years, location_compatibility,
                    salary_compatibility, availability_match, recommendation, match_reasons,
                    concern_areas
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                ) ON CONFLICT (candidate_id, job_id) DO UPDATE SET
                    overall_match_score = EXCLUDED.overall_match_score,
                    skill_match_score = EXCLUDED.skill_match_score,
                    experience_match_score = EXCLUDED.experience_match_score,
                    location_match_score = EXCLUDED.location_match_score,
                    education_match_score = EXCLUDED.education_match_score,
                    salary_match_score = EXCLUDED.salary_match_score,
                    matching_skills = EXCLUDED.matching_skills,
                    missing_skills = EXCLUDED.missing_skills,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            async with conn.transaction():
                for match in matches:
                    await conn.execute(
                        query,
                        match.candidate_id, match.job_id, match.overall_match_score,
                        match.skill_match_score, match.experience_match_score,
                        match.location_match_score, match.education_match_score,
                        match.salary_match_score, json.dumps(match.matching_skills),
                        json.dumps(match.missing_skills), match.skill_gap_percentage,
                        match.experience_fit, match.experience_gap_years,
                        match.location_compatibility, match.salary_compatibility,
                        match.availability_match, match.recommendation,
                        json.dumps(match.match_reasons), json.dumps(match.concern_areas)
                    )
            
            logger.info(f"Saved {len(matches)} match results")
    
    async def get_top_matches(
        self, 
        job_id: int, 
        limit: int = 20, 
        min_score: float = 0.6
    ) -> List[Dict]:
        """Get top matching candidates for a job"""
        async with self.get_connection() as conn:
            query = """
                SELECT 
                    c.id as candidate_id, c.name, c.email, c.experience_years,
                    c.location, c.skills, m.overall_match_score, m.skill_match_score,
                    m.matching_skills, m.missing_skills, m.recommendation
                FROM candidates c
                JOIN match_results m ON c.id = m.candidate_id
                WHERE m.job_id = $1 AND m.overall_match_score >= $2
                ORDER BY m.overall_match_score DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, job_id, min_score, limit)
            
            matches = []
            for row in rows:
                match = dict(row)
                match['skills'] = json.loads(match['skills'] or '[]')
                match['matching_skills'] = json.loads(match['matching_skills'] or '[]')
                match['missing_skills'] = json.loads(match['missing_skills'] or '[]')
                matches.append(match)
            
            return matches
    
    async def search_candidates(
        self,
        query: str = "",
        skills: List[str] = None,
        experience_min: int = None,
        experience_max: int = None,
        location: str = None,
        education_level: str = None,
        availability: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Advanced candidate search with multiple filters"""
        async with self.get_connection() as conn:
            base_query = """
                SELECT 
                    id, name, email, phone, location, experience_years,
                    skills, education_level, current_position, salary_expectation,
                    availability_date, overall_score
                FROM candidates
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            # Text search
            if query:
                param_count += 1
                base_query += f"""
                    AND (
                        name ILIKE ${param_count} OR 
                        resume_text ILIKE ${param_count} OR
                        current_position ILIKE ${param_count}
                    )
                """
                params.append(f"%{query}%")
            
            # Skills filter
            if skills:
                param_count += 1
                base_query += f" AND skills::jsonb ?| ${param_count}"
                params.append(skills)
            
            # Experience filter
            if experience_min is not None:
                param_count += 1
                base_query += f" AND experience_years >= ${param_count}"
                params.append(experience_min)
            
            if experience_max is not None:
                param_count += 1
                base_query += f" AND experience_years <= ${param_count}"
                params.append(experience_max)
            
            # Location filter
            if location:
                param_count += 1
                base_query += f" AND location ILIKE ${param_count}"
                params.append(f"%{location}%")
            
            # Education filter
            if education_level:
                param_count += 1
                base_query += f" AND education_level = ${param_count}"
                params.append(education_level)
            
            # Availability filter
            if availability:
                param_count += 1
                if availability.lower() == "immediate":
                    base_query += f" AND (availability_date IS NULL OR availability_date <= CURRENT_DATE)"
                else:
                    base_query += f" AND availability_date <= ${param_count}::date"
                    params.append(availability)
            
            base_query += f" ORDER BY overall_score DESC NULLS LAST LIMIT ${param_count + 1}"
            params.append(limit)
            
            rows = await conn.fetch(base_query, *params)
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                candidate['skills'] = json.loads(candidate['skills'] or '[]')
                candidates.append(candidate)
            
            return candidates
    
    async def get_candidate_profile(self, candidate_id: int) -> Optional[Dict]:
        """Get detailed candidate profile"""
        async with self.get_connection() as conn:
            # Get candidate details
            candidate_query = """
                SELECT * FROM candidates WHERE id = $1
            """
            candidate_row = await conn.fetchrow(candidate_query, candidate_id)
            
            if not candidate_row:
                return None
            
            candidate = dict(candidate_row)
            
            # Parse JSON fields
            json_fields = ['skills', 'certifications', 'languages', 'education', 'portfolio_links', 'preferred_locations']
            for field in json_fields:
                if candidate.get(field):
                    candidate[field] = json.loads(candidate[field])
                else:
                    candidate[field] = []
            
            # Get applications
            apps_query = """
                SELECT a.*, j.title as job_title, j.company
                FROM applications a
                JOIN job_postings j ON a.job_id = j.id
                WHERE a.candidate_id = $1
                ORDER BY a.application_date DESC
                LIMIT 10
            """
            app_rows = await conn.fetch(apps_query, candidate_id)
            candidate['applications'] = [dict(row) for row in app_rows]
            
            return candidate
    
    async def update_application_status(
        self,
        application_id: int,
        status: str,
        notes: str = "",
        next_action: str = ""
    ) -> bool:
        """Update application status and add notes"""
        async with self.get_connection() as conn:
            query = """
                UPDATE applications 
                SET status = $1, notes = array_append(notes, $2), next_action = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
                RETURNING id
            """
            
            result = await conn.fetchval(query, status, notes, next_action, application_id)
            return result is not None
    
    async def get_analytics_data(
        self,
        date_range: str = "30d",
        job_id: int = None,
        department: str = None
    ) -> Dict:
        """Get analytics data for dashboard"""
        async with self.get_connection() as conn:
            # Parse date range
            if date_range.endswith('d'):
                days = int(date_range[:-1])
                date_filter = f"CURRENT_DATE - INTERVAL '{days} days'"
            else:
                date_filter = "CURRENT_DATE - INTERVAL '30 days'"
            
            analytics = {}
            
            # Basic counts
            analytics['total_candidates'] = await conn.fetchval(
                f"SELECT COUNT(*) FROM candidates WHERE created_at >= {date_filter}"
            )
            
            analytics['active_jobs'] = await conn.fetchval(
                "SELECT COUNT(*) FROM job_postings WHERE status = 'Open'"
            )
            
            analytics['total_applications'] = await conn.fetchval(
                f"SELECT COUNT(*) FROM applications WHERE application_date >= {date_filter}"
            )
            
            analytics['interviews_scheduled'] = await conn.fetchval(
                f"SELECT COUNT(*) FROM interviews WHERE scheduled_date >= {date_filter} AND status = 'Scheduled'"
            )
            
            # Calculate hiring rate
            hires = await conn.fetchval(
                f"SELECT COUNT(*) FROM applications WHERE decision = 'Hired' AND decision_date >= {date_filter}"
            )
            total_decisions = await conn.fetchval(
                f"SELECT COUNT(*) FROM applications WHERE decision IS NOT NULL AND decision_date >= {date_filter}"
            )
            analytics['hiring_rate'] = hires / total_decisions if total_decisions > 0 else 0
            
            # Top skills in demand
            skills_query = """
                SELECT unnest(required_skills::text[]) as skill, COUNT(*) as demand
                FROM job_postings 
                WHERE status = 'Open'
                GROUP BY skill
                ORDER BY demand DESC
                LIMIT 10
            """
            skills_rows = await conn.fetch(skills_query)
            analytics['top_skills'] = [{'name': row['skill'], 'demand': row['demand']} for row in skills_rows]
            
            # Recent activity (placeholder)
            analytics['recent_activity'] = [
                {'timestamp': '2024-01-01 10:00', 'description': 'New candidate application received'},
                {'timestamp': '2024-01-01 09:30', 'description': 'Interview scheduled'},
                {'timestamp': '2024-01-01 09:00', 'description': 'Job posting published'},
            ]
            
            # Source performance (placeholder)
            analytics['top_sources'] = [
                {'name': 'LinkedIn', 'candidates': 150, 'quality_score': 8.5},
                {'name': 'Indeed', 'candidates': 120, 'quality_score': 7.2},
                {'name': 'Company Website', 'candidates': 80, 'quality_score': 9.1},
            ]
            
            return analytics


async def init_database():
    """Initialize database schema with optimizations for large datasets"""
    # Load environment variables from parent directory
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'recruitment_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'techy@123')
    }
    
    try:
        conn = await asyncpg.connect(**db_config)
        
        # Create tables with optimizations for large datasets
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                location VARCHAR(100),
                
                -- Professional Information
                current_position VARCHAR(200),
                experience_years INTEGER DEFAULT 0,
                skills JSONB DEFAULT '[]'::jsonb,
                certifications JSONB DEFAULT '[]'::jsonb,
                languages JSONB DEFAULT '[]'::jsonb,
                
                -- Education
                education JSONB DEFAULT '[]'::jsonb,
                education_level VARCHAR(50),
                
                -- Resume and Portfolio
                resume_text TEXT,
                resume_file_path VARCHAR(500),
                portfolio_links JSONB DEFAULT '[]'::jsonb,
                
                -- Preferences
                salary_expectation INTEGER,
                preferred_locations JSONB DEFAULT '[]'::jsonb,
                remote_preference BOOLEAN DEFAULT false,
                availability_date DATE,
                
                -- Metadata
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Scoring
                overall_score DECIMAL(5,2),
                technical_score DECIMAL(5,2),
                communication_score DECIMAL(5,2)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS job_postings (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                company VARCHAR(100) NOT NULL,
                department VARCHAR(100),
                
                -- Job Details
                description TEXT NOT NULL,
                responsibilities JSONB DEFAULT '[]'::jsonb,
                requirements JSONB DEFAULT '[]'::jsonb,
                
                -- Skills and Experience
                required_skills JSONB NOT NULL,
                preferred_skills JSONB DEFAULT '[]'::jsonb,
                experience_min INTEGER DEFAULT 0,
                experience_max INTEGER DEFAULT 10,
                
                -- Education and Certifications
                education_requirements TEXT,
                certifications JSONB DEFAULT '[]'::jsonb,
                
                -- Compensation and Benefits
                salary_min INTEGER,
                salary_max INTEGER,
                benefits JSONB DEFAULT '[]'::jsonb,
                
                -- Location and Work Style
                location VARCHAR(100),
                remote_ok BOOLEAN DEFAULT false,
                hybrid_ok BOOLEAN DEFAULT false,
                travel_required VARCHAR(50),
                
                -- Job Metadata
                job_type VARCHAR(50) DEFAULT 'Full-time',
                employment_type VARCHAR(50) DEFAULT 'Permanent',
                industry VARCHAR(100),
                seniority_level VARCHAR(50),
                
                -- Application Details
                application_deadline DATE,
                start_date DATE,
                urgency VARCHAR(20) DEFAULT 'Normal',
                
                -- Status and Tracking
                status VARCHAR(20) DEFAULT 'Open',
                posted_date DATE DEFAULT CURRENT_DATE,
                filled_date DATE,
                hiring_manager VARCHAR(100),
                recruiter VARCHAR(100),
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
                job_id INTEGER REFERENCES job_postings(id) ON DELETE CASCADE,
                
                -- Application Details
                application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'Applied',
                source VARCHAR(100),
                
                -- Documents
                cover_letter TEXT,
                additional_documents JSONB DEFAULT '[]'::jsonb,
                
                -- Scoring and Assessment
                initial_score DECIMAL(5,2),
                screening_score DECIMAL(5,2),
                interview_scores JSONB DEFAULT '{}'::jsonb,
                final_score DECIMAL(5,2),
                
                -- Process Tracking
                screening_completed BOOLEAN DEFAULT false,
                interviews_completed INTEGER DEFAULT 0,
                references_checked BOOLEAN DEFAULT false,
                background_check_completed BOOLEAN DEFAULT false,
                
                -- Decision Making
                recommendation TEXT,
                decision VARCHAR(50),
                decision_date TIMESTAMP,
                decision_maker VARCHAR(100),
                
                -- Communication
                last_contact_date TIMESTAMP,
                next_action TEXT,
                notes TEXT[],
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(candidate_id, job_id)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id SERIAL PRIMARY KEY,
                application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
                
                -- Interview Details
                interview_type VARCHAR(50) NOT NULL,
                scheduled_date TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                interviewer VARCHAR(100) NOT NULL,
                interview_panel JSONB DEFAULT '[]'::jsonb,
                
                -- Location/Method
                location VARCHAR(200),
                meeting_link VARCHAR(500),
                phone_number VARCHAR(20),
                
                -- Preparation
                preparation_materials JSONB DEFAULT '[]'::jsonb,
                technical_requirements JSONB DEFAULT '[]'::jsonb,
                
                -- Status and Feedback
                status VARCHAR(20) DEFAULT 'Scheduled',
                feedback TEXT,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                recommendation TEXT,
                
                -- Follow-up
                next_steps TEXT,
                follow_up_date TIMESTAMP,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS match_results (
                id SERIAL PRIMARY KEY,
                candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
                job_id INTEGER REFERENCES job_postings(id) ON DELETE CASCADE,
                
                -- Scoring
                overall_match_score DECIMAL(5,2) NOT NULL,
                skill_match_score DECIMAL(5,2),
                experience_match_score DECIMAL(5,2),
                location_match_score DECIMAL(5,2),
                education_match_score DECIMAL(5,2),
                salary_match_score DECIMAL(5,2),
                
                -- Detailed Analysis
                matching_skills JSONB DEFAULT '[]'::jsonb,
                missing_skills JSONB DEFAULT '[]'::jsonb,
                skill_gap_percentage DECIMAL(5,2) DEFAULT 0,
                
                -- Experience Analysis
                experience_fit VARCHAR(50),
                experience_gap_years INTEGER DEFAULT 0,
                
                -- Other Factors
                location_compatibility BOOLEAN DEFAULT true,
                salary_compatibility BOOLEAN DEFAULT true,
                availability_match BOOLEAN DEFAULT true,
                
                -- Recommendation
                recommendation VARCHAR(100),
                match_reasons JSONB DEFAULT '[]'::jsonb,
                concern_areas JSONB DEFAULT '[]'::jsonb,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(candidate_id, job_id)
            )
        """)
        
        # Create indexes for performance optimization
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates USING GIN(skills)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(experience_years)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at)")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_postings_status ON job_postings(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_postings_skills ON job_postings USING GIN(required_skills)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_postings_company ON job_postings(company)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_postings_location ON job_postings(location)")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_candidate_job ON applications(candidate_id, job_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_date ON applications(application_date)")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_match_results_score ON match_results(overall_match_score)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_match_results_job ON match_results(job_id)")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviews_scheduled ON interviews(scheduled_date)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status)")
        
        logger.info("Database schema initialized successfully with performance optimizations")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        if 'conn' in locals():
            await conn.close()
