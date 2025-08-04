"""
Workflow Automation for Enterprise Recruitment Agent

Handles automated processes including screening, interview scheduling,
email notifications, and workflow management for high-volume recruitment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database import DatabaseManager
from models import ApplicationStatus, InterviewType, ScreeningCriteria
from email_service import EmailService

logger = logging.getLogger(__name__)


class WorkflowAutomation:
    """Advanced workflow automation for recruitment processes"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.email_service = EmailService()
        
        # Default screening criteria
        self.default_screening = {
            'min_experience_years': 0,
            'required_skills_match_threshold': 0.5,
            'education_required': False,
            'location_match_required': False,
            'salary_compatibility_required': True
        }
        
        # Interview scheduling preferences
        self.interview_preferences = {
            'default_duration': 60,  # minutes
            'buffer_time': 15,       # minutes between interviews
            'daily_interview_limit': 8,
            'working_hours': (9, 17),  # 9 AM to 5 PM
            'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
        }
    
    async def automated_screening(
        self,
        job_id: int,
        candidate_ids: Optional[List[int]] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Run automated screening on candidates for a job"""
        
        logger.info(f"Starting automated screening for job {job_id}")
        
        # Merge criteria with defaults
        screening_criteria = {**self.default_screening, **(criteria or {})}
        
        # Get job details
        job_details = await self._get_job_details(job_id)
        if not job_details:
            raise ValueError(f"Job {job_id} not found")
        
        # Get candidates to screen
        if candidate_ids:
            candidates = await self._get_specific_candidates(candidate_ids)
        else:
            candidates = await self._get_job_applicants(job_id)
        
        if not candidates:
            logger.warning(f"No candidates found for screening job {job_id}")
            return []
        
        # Screen each candidate
        screening_results = []
        
        for candidate in candidates:
            result = await self._screen_candidate(
                candidate, job_details, screening_criteria
            )
            screening_results.append(result)
        
        # Update application statuses based on screening results
        await self._update_screening_statuses(screening_results)
        
        logger.info(f"Screening completed for {len(screening_results)} candidates")
        
        return screening_results
    
    async def schedule_bulk_interviews(
        self,
        candidate_ids: List[int],
        job_id: int,
        interviewer: str,
        interview_type: str = "Phone Screen",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Schedule interviews for multiple candidates automatically"""
        
        logger.info(f"Scheduling interviews for {len(candidate_ids)} candidates")
        
        # Parse date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() + timedelta(days=1)  # Tomorrow
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = start_dt + timedelta(days=14)  # 2 weeks from start
        
        # Generate available time slots
        available_slots = self._generate_time_slots(
            start_dt, end_dt, duration_minutes
        )
        
        if len(available_slots) < len(candidate_ids):
            logger.warning(f"Only {len(available_slots)} slots available for {len(candidate_ids)} candidates")
        
        # Get candidate details
        candidates = await self._get_specific_candidates(candidate_ids)
        
        # Schedule interviews
        scheduled_interviews = []
        
        for i, candidate in enumerate(candidates):
            if i >= len(available_slots):
                logger.warning(f"No more slots available for candidate {candidate['id']}")
                break
            
            slot = available_slots[i]
            
            # Create interview record
            interview_data = {
                'candidate_id': candidate['id'],
                'candidate_name': candidate['name'],
                'job_id': job_id,
                'interviewer': interviewer,
                'interview_type': interview_type,
                'scheduled_time': slot,
                'duration_minutes': duration_minutes
            }
            
            # Save to database
            interview_id, app_id = await self._create_interview_record(interview_data)
            interview_data['interview_id'] = interview_id
            interview_data['application_id'] = app_id
            
            scheduled_interviews.append(interview_data)
        
        # Send notifications (placeholder)
        await self._send_interview_notifications(scheduled_interviews)
        
        logger.info(f"Successfully scheduled {len(scheduled_interviews)} interviews")
        
        return scheduled_interviews
    
    async def auto_update_application_status(
        self,
        application_id: int,
        new_status: str,
        trigger_next_action: bool = True
    ) -> Dict[str, Any]:
        """Automatically update application status and trigger next actions"""
        
        async with self.db_manager.get_connection() as conn:
            # Get current application details
            app_query = """
                SELECT a.*, c.name as candidate_name, j.title as job_title
                FROM applications a
                JOIN candidates c ON a.candidate_id = c.id
                JOIN job_postings j ON a.job_id = j.id
                WHERE a.id = $1
            """
            
            app_row = await conn.fetchrow(app_query, application_id)
            
            if not app_row:
                raise ValueError(f"Application {application_id} not found")
            
            current_status = app_row['status']
            
            # Update status
            update_query = """
                UPDATE applications 
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """
            
            await conn.execute(update_query, new_status, application_id)
            
            # Trigger next actions based on new status
            next_actions = []
            
            if trigger_next_action:
                next_actions = await self._trigger_status_actions(
                    app_row, current_status, new_status
                )
            
            logger.info(f"Updated application {application_id} from {current_status} to {new_status}")
            
            return {
                'application_id': application_id,
                'candidate_name': app_row['candidate_name'],
                'job_title': app_row['job_title'],
                'old_status': current_status,
                'new_status': new_status,
                'next_actions': next_actions
            }
    
    async def _screen_candidate(
        self,
        candidate: Dict[str, Any],
        job_details: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Screen a single candidate against job requirements"""
        
        score = 0.0
        max_score = 10.0
        passed = True
        failure_reasons = []
        
        # Experience screening
        min_exp = criteria.get('min_experience_years', 0)
        candidate_exp = candidate.get('experience_years', 0)
        
        if candidate_exp >= min_exp:
            exp_score = min(candidate_exp / max(job_details.get('experience_max', 10), 1), 1.0) * 3
            score += exp_score
        else:
            score += 0
            if min_exp > 0:
                failure_reasons.append(f"Insufficient experience: {candidate_exp} < {min_exp} years")
                passed = False
        
        # Skills screening
        candidate_skills = candidate.get('skills', [])
        required_skills = job_details.get('required_skills', [])
        
        if required_skills:
            matching_skills = [skill for skill in required_skills if skill in candidate_skills]
            skill_match_ratio = len(matching_skills) / len(required_skills)
            
            threshold = criteria.get('required_skills_match_threshold', 0.5)
            
            if skill_match_ratio >= threshold:
                score += skill_match_ratio * 4
            else:
                score += skill_match_ratio * 2
                missing_skills = [skill for skill in required_skills if skill not in candidate_skills]
                failure_reasons.append(f"Missing skills: {', '.join(missing_skills[:3])}")
                if skill_match_ratio < threshold:
                    passed = False
        else:
            score += 2  # No specific skills required
        
        # Education screening
        if criteria.get('education_required', False):
            education_level = candidate.get('education_level')
            job_education = job_details.get('education_requirements', '').lower()
            
            if education_level:
                # Simplified education matching
                if ('bachelor' in job_education and education_level in ['Bachelors', 'Masters', 'PhD']) or \
                   ('master' in job_education and education_level in ['Masters', 'PhD']) or \
                   ('phd' in job_education and education_level == 'PhD'):
                    score += 2
                else:
                    score += 1
                    failure_reasons.append("Education requirements not fully met")
            else:
                failure_reasons.append("No education information available")
                passed = False
        else:
            score += 1  # Bonus for having education info
        
        # Location screening
        if criteria.get('location_match_required', False) and not job_details.get('remote_ok', False):
            candidate_location = candidate.get('location', '').lower()
            job_location = job_details.get('location', '').lower()
            
            if candidate_location and job_location:
                if any(part in job_location for part in candidate_location.split(',')):
                    score += 1
                else:
                    failure_reasons.append("Location mismatch")
                    passed = False
            else:
                failure_reasons.append("Location information incomplete")
                passed = False
        else:
            score += 0.5  # Neutral if remote ok or not required
        
        # Overall score and decision
        final_score = min(score, max_score)
        
        # Auto-reject threshold
        auto_reject_threshold = criteria.get('auto_reject_threshold', 3.0)
        auto_advance_threshold = criteria.get('auto_advance_threshold', 8.0)
        
        if final_score < auto_reject_threshold:
            decision = "Auto-Reject"
            passed = False
        elif final_score >= auto_advance_threshold:
            decision = "Auto-Advance"
            passed = True
        else:
            decision = "Manual Review"
        
        return {
            'candidate_id': candidate['id'],
            'name': candidate['name'],
            'email': candidate['email'],
            'score': round(final_score, 2),
            'max_score': max_score,
            'passed': passed,
            'decision': decision,
            'failure_reasons': failure_reasons,
            'matching_skills': [skill for skill in (job_details.get('required_skills', [])) if skill in candidate_skills],
            'experience_years': candidate_exp,
            'screening_date': datetime.now()
        }
    
    async def _get_job_details(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job details for screening"""
        async with self.db_manager.get_connection() as conn:
            query = """
                SELECT 
                    id, title, required_skills, preferred_skills, experience_min,
                    experience_max, education_requirements, location, remote_ok,
                    salary_min, salary_max
                FROM job_postings 
                WHERE id = $1
            """
            
            row = await conn.fetchrow(query, job_id)
            
            if row:
                job = dict(row)
                # Parse JSON fields
                import json
                job['required_skills'] = json.loads(job.get('required_skills') or '[]')
                job['preferred_skills'] = json.loads(job.get('preferred_skills') or '[]')
                return job
            
            return None
    
    async def _get_specific_candidates(self, candidate_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific candidates by IDs"""
        async with self.db_manager.get_connection() as conn:
            query = """
                SELECT 
                    id, name, email, skills, experience_years, education_level,
                    location, salary_expectation, overall_score
                FROM candidates 
                WHERE id = ANY($1)
            """
            
            rows = await conn.fetch(query, candidate_ids)
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                # Parse JSON fields
                import json
                candidate['skills'] = json.loads(candidate.get('skills') or '[]')
                candidates.append(candidate)
            
            return candidates
    
    async def _get_job_applicants(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all applicants for a job"""
        async with self.db_manager.get_connection() as conn:
            query = """
                SELECT 
                    c.id, c.name, c.email, c.skills, c.experience_years,
                    c.education_level, c.location, c.salary_expectation,
                    c.overall_score, a.status as application_status
                FROM candidates c
                JOIN applications a ON c.id = a.candidate_id
                WHERE a.job_id = $1
                AND a.status = 'Applied'
            """
            
            rows = await conn.fetch(query, job_id)
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                # Parse JSON fields
                import json
                candidate['skills'] = json.loads(candidate.get('skills') or '[]')
                candidates.append(candidate)
            
            return candidates
    
    async def _update_screening_statuses(self, screening_results: List[Dict[str, Any]]) -> None:
        """Update application statuses based on screening results"""
        async with self.db_manager.get_connection() as conn:
            for result in screening_results:
                new_status = "Screening"
                
                if result['decision'] == "Auto-Reject":
                    new_status = "Rejected"
                elif result['decision'] == "Auto-Advance":
                    new_status = "Phone Screen"
                else:
                    new_status = "Manual Review"
                
                # Update application status
                update_query = """
                    UPDATE applications 
                    SET 
                        status = $1,
                        screening_completed = true,
                        screening_score = $2,
                        screening_notes = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE candidate_id = $4 
                    AND job_id = (
                        SELECT job_id FROM applications 
                        WHERE candidate_id = $4 LIMIT 1
                    )
                """
                
                notes = f"Automated screening: {result['decision']}. Score: {result['score']}/{result['max_score']}"
                if result['failure_reasons']:
                    notes += f". Issues: {'; '.join(result['failure_reasons'])}"
                
                await conn.execute(
                    update_query,
                    new_status,
                    result['score'],
                    notes,
                    result['candidate_id']
                )
    
    def _generate_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int
    ) -> List[datetime]:
        """Generate available time slots for interviews"""
        
        slots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_date:
            # Check if it's a working day
            if current_date.weekday() in self.interview_preferences['working_days']:
                
                # Generate slots for this day
                start_hour, end_hour = self.interview_preferences['working_hours']
                current_time = current_date.replace(hour=start_hour)
                end_time = current_date.replace(hour=end_hour)
                
                daily_slots = 0
                max_daily_slots = self.interview_preferences['daily_interview_limit']
                
                while current_time < end_time and daily_slots < max_daily_slots:
                    # Add slot if it's in the future
                    if current_time > datetime.now():
                        slots.append(current_time)
                        daily_slots += 1
                    
                    # Move to next slot
                    current_time += timedelta(
                        minutes=duration_minutes + self.interview_preferences['buffer_time']
                    )
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return slots
    
    async def _create_interview_record(self, interview_data: Dict[str, Any]) -> Tuple[int, int]:
        """Create interview record in database and return (interview_id, application_id)"""
        async with self.db_manager.get_connection() as conn:
            # First, ensure there's an application record
            app_query = """
                INSERT INTO applications (candidate_id, job_id, status)
                VALUES ($1, $2, 'Interview Scheduled')
                ON CONFLICT (candidate_id, job_id) DO UPDATE SET
                    status = 'Interview Scheduled',
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            app_id = await conn.fetchval(
                app_query,
                interview_data['candidate_id'],
                interview_data['job_id']
            )
            
            # Create interview record
            interview_query = """
                INSERT INTO interviews (
                    application_id, interview_type, scheduled_date,
                    interviewer, duration_minutes, status
                ) VALUES ($1, $2, $3, $4, $5, 'Scheduled')
                RETURNING id
            """
            
            interview_id = await conn.fetchval(
                interview_query,
                app_id,
                interview_data['interview_type'],
                interview_data['scheduled_time'],
                interview_data['interviewer'],
                interview_data['duration_minutes']
            )
            
            return interview_id, app_id
    
    async def _send_interview_notifications(self, interviews: List[Dict[str, Any]]) -> None:
        """Send interview notifications via email"""
        
        for interview in interviews:
            try:
                # Get candidate details
                async with self.db_manager.get_connection() as conn:
                    candidate_query = """
                        SELECT c.name, c.email, j.title as job_title
                        FROM candidates c
                        JOIN applications a ON c.id = a.candidate_id
                        JOIN job_postings j ON a.job_id = j.id
                        WHERE a.id = $1
                    """
                    candidate_result = await conn.fetchrow(candidate_query, interview['application_id'])
                    
                    if candidate_result:
                        # Format interview details for email
                        interview_details = {
                            'job_title': candidate_result['job_title'],
                            'interviewer': interview['interviewer'],
                            'date': interview['scheduled_time'].strftime('%A, %B %d, %Y'),
                            'time': interview['scheduled_time'].strftime('%I:%M %p'),
                            'duration': f"{interview['duration_minutes']} minutes",
                            'type': interview['interview_type'],
                            'meeting_link': interview.get('meeting_link', '')
                        }
                        
                        # Send email confirmation
                        success = await self.email_service.send_interview_confirmation(
                            candidate_result['email'],
                            candidate_result['name'],
                            interview_details
                        )
                        
                        if success:
                            logger.info(f"✅ Interview confirmation sent to {candidate_result['name']}")
                        else:
                            logger.error(f"❌ Failed to send confirmation to {candidate_result['name']}")
                    
            except Exception as e:
                logger.error(f"Error sending interview notification: {str(e)}")
        
        logger.info(f"📧 Processed notifications for {len(interviews)} interviews")
    
    async def _trigger_status_actions(
        self,
        application: Dict[str, Any],
        old_status: str,
        new_status: str
    ) -> List[str]:
        """Trigger automated actions based on status changes"""
        
        actions = []
        
        # Status-specific automation
        if new_status == "Phone Screen":
            actions.append("Auto-schedule phone screen within 3 business days")
            
        elif new_status == "Technical Interview":
            actions.append("Send technical assessment link")
            actions.append("Schedule technical interview")
            
        elif new_status == "Final Interview":
            actions.append("Schedule final interview with hiring manager")
            actions.append("Request references")
            
        elif new_status == "Offer Pending":
            actions.append("Generate offer letter")
            actions.append("Schedule offer call")
            
        elif new_status == "Rejected":
            actions.append("Send rejection email")
            actions.append("Add to talent pool for future roles")
            
        elif new_status == "Hired":
            actions.append("Send welcome package")
            actions.append("Initiate onboarding process")
            actions.append("Close job posting if target met")
        
        # Log actions for audit trail
        for action in actions:
            logger.info(f"Triggered action for application {application['id']}: {action}")
        
        return actions
