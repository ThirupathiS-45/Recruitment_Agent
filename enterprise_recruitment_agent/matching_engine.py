"""
AI-powered matching engine for candidate-job matching

Uses advanced algorithms including semantic similarity, skill matching,
and experience compatibility to find the best candidates for jobs.
"""

import asyncio
import json
import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from models import MatchResult, CandidateProfile, JobPosting
from database import DatabaseManager

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Advanced AI-powered candidate-job matching engine"""
    
    def __init__(self):
        self.skill_weights = {
            'exact_match': 1.0,
            'related_match': 0.7,
            'category_match': 0.5
        }
        
        # Skill relationships for better matching
        self.skill_relationships = {
            'React': ['JavaScript', 'JSX', 'Redux', 'HTML', 'CSS'],
            'Angular': ['TypeScript', 'JavaScript', 'HTML', 'CSS', 'RxJS'],
            'Vue.js': ['JavaScript', 'HTML', 'CSS', 'Vuex'],
            'Python': ['Django', 'Flask', 'FastAPI', 'NumPy', 'Pandas'],
            'Java': ['Spring', 'Hibernate', 'Maven', 'Gradle'],
            'Node.js': ['JavaScript', 'Express', 'npm', 'REST APIs'],
            'AWS': ['Cloud Computing', 'EC2', 'S3', 'Lambda', 'RDS'],
            'Docker': ['Containerization', 'Kubernetes', 'DevOps'],
            'Machine Learning': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn'],
            'Data Science': ['Python', 'R', 'Pandas', 'NumPy', 'Statistics']
        }
        
        # Experience level mappings
        self.experience_levels = {
            'entry': (0, 2),
            'junior': (1, 3),
            'mid': (3, 6),
            'senior': (5, 10),
            'lead': (7, 15),
            'principal': (10, 20)
        }
    
    async def find_best_matches(
        self,
        job_id: int,
        db_manager: DatabaseManager,
        limit: int = 20,
        min_score: float = 0.6,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Find the best matching candidates for a job"""
        
        # Get job details
        job = await self._get_job_details(job_id, db_manager)
        if not job:
            logger.error(f"Job {job_id} not found")
            return []
        
        # Get candidates for matching
        candidates = await db_manager.get_candidates_for_matching(job_id, filters)
        
        if not candidates:
            logger.info(f"No candidates found for job {job_id}")
            return []
        
        # Calculate match scores for all candidates
        match_results = []
        
        for candidate in candidates:
            match_result = await self._calculate_match_score(candidate, job)
            
            if match_result.overall_match_score >= min_score:
                match_results.append({
                    'candidate_id': candidate['id'],
                    'candidate_name': candidate['name'],
                    'email': candidate['email'],
                    'experience_years': candidate['experience_years'],
                    'location': candidate.get('location'),
                    'match_score': match_result.overall_match_score,
                    'skill_match': match_result.skill_match_score,
                    'experience_match': match_result.experience_match_score,
                    'location_match': match_result.location_match_score,
                    'matching_skills': match_result.matching_skills,
                    'missing_skills': match_result.missing_skills,
                    'recommendation': match_result.recommendation,
                    'match_reasons': match_result.match_reasons,
                    'concern_areas': match_result.concern_areas
                })
        
        # Sort by match score and return top matches
        match_results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Save match results to database
        match_objects = []
        for result in match_results[:limit]:
            match_obj = MatchResult(
                candidate_id=result['candidate_id'],
                job_id=job_id,
                candidate_name=result['candidate_name'],
                job_title=job['title'],
                overall_match_score=result['match_score'],
                skill_match_score=result['skill_match'],
                experience_match_score=result['experience_match'],
                location_match_score=result['location_match'],
                education_match_score=0.8,  # Placeholder
                salary_match_score=0.8,     # Placeholder
                matching_skills=result['matching_skills'],
                missing_skills=result['missing_skills'],
                recommendation=result['recommendation'],
                match_reasons=result['match_reasons'],
                concern_areas=result['concern_areas'],
                created_at=datetime.now()
            )
            match_objects.append(match_obj)
        
        await db_manager.save_match_results(match_objects)
        
        return match_results[:limit]
    
    async def get_top_matches(
        self,
        job_id: int,
        db_manager: DatabaseManager,
        limit: int = 10
    ) -> List[Dict]:
        """Get previously calculated top matches from database"""
        return await db_manager.get_top_matches(job_id, limit)
    
    async def _get_job_details(self, job_id: int, db_manager: DatabaseManager) -> Optional[Dict]:
        """Get job details for matching"""
        async with db_manager.get_connection() as conn:
            query = """
                SELECT 
                    id, title, company, description, required_skills, preferred_skills,
                    experience_min, experience_max, location, remote_ok, salary_min,
                    salary_max, education_requirements, certifications
                FROM job_postings 
                WHERE id = $1
            """
            
            row = await conn.fetchrow(query, job_id)
            if not row:
                return None
            
            job = dict(row)
            job['required_skills'] = json.loads(job['required_skills'] or '[]')
            job['preferred_skills'] = json.loads(job['preferred_skills'] or '[]')
            job['certifications'] = json.loads(job['certifications'] or '[]')
            
            return job
    
    async def _calculate_match_score(self, candidate: Dict, job: Dict) -> MatchResult:
        """Calculate comprehensive match score between candidate and job"""
        
        # Extract candidate skills
        candidate_skills = candidate.get('skills', [])
        if isinstance(candidate_skills, str):
            candidate_skills = json.loads(candidate_skills)
        
        # Calculate individual scores
        skill_score, matching_skills, missing_skills = self._calculate_skill_match(
            candidate_skills, job['required_skills'], job['preferred_skills']
        )
        
        experience_score, experience_fit, experience_gap = self._calculate_experience_match(
            candidate['experience_years'], job['experience_min'], job['experience_max']
        )
        
        location_score, location_compatible = self._calculate_location_match(
            candidate.get('location'), job.get('location'), job.get('remote_ok', False)
        )
        
        education_score = self._calculate_education_match(
            candidate.get('education_level'), job.get('education_requirements')
        )
        
        salary_score, salary_compatible = self._calculate_salary_match(
            candidate.get('salary_expectation'), job.get('salary_min'), job.get('salary_max')
        )
        
        # Calculate weighted overall score
        weights = {
            'skills': 0.4,
            'experience': 0.25,
            'location': 0.15,
            'education': 0.1,
            'salary': 0.1
        }
        
        overall_score = (
            skill_score * weights['skills'] +
            experience_score * weights['experience'] +
            location_score * weights['location'] +
            education_score * weights['education'] +
            salary_score * weights['salary']
        )
        
        # Generate recommendation and reasons
        recommendation, reasons, concerns = self._generate_recommendation(
            overall_score, skill_score, experience_score, location_score,
            matching_skills, missing_skills, experience_fit
        )
        
        return MatchResult(
            candidate_id=candidate['id'],
            job_id=job['id'],
            candidate_name=candidate['name'],
            job_title=job['title'],
            overall_match_score=round(overall_score, 3),
            skill_match_score=round(skill_score, 3),
            experience_match_score=round(experience_score, 3),
            location_match_score=round(location_score, 3),
            education_match_score=round(education_score, 3),
            salary_match_score=round(salary_score, 3),
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            skill_gap_percentage=round((len(missing_skills) / max(len(job['required_skills']), 1)) * 100, 1),
            experience_fit=experience_fit,
            experience_gap_years=experience_gap,
            location_compatibility=location_compatible,
            salary_compatibility=salary_compatible,
            recommendation=recommendation,
            match_reasons=reasons,
            concern_areas=concerns
        )
    
    def _calculate_skill_match(
        self, 
        candidate_skills: List[str], 
        required_skills: List[str], 
        preferred_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate skill match score with semantic understanding"""
        
        if not required_skills:
            return 1.0, [], []
        
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        preferred_skills_lower = [skill.lower() for skill in preferred_skills]
        
        matching_skills = []
        missing_skills = []
        total_score = 0.0
        
        # Check required skills
        for req_skill in required_skills:
            req_skill_lower = req_skill.lower()
            skill_score = 0.0
            
            # Exact match
            if req_skill_lower in candidate_skills_lower:
                skill_score = self.skill_weights['exact_match']
                matching_skills.append(req_skill)
            else:
                # Check for related skills
                related_score = self._find_related_skill_match(req_skill, candidate_skills)
                if related_score > 0:
                    skill_score = related_score
                    matching_skills.append(req_skill)
                else:
                    missing_skills.append(req_skill)
            
            total_score += skill_score
        
        # Bonus for preferred skills
        preferred_bonus = 0.0
        for pref_skill in preferred_skills:
            pref_skill_lower = pref_skill.lower()
            if pref_skill_lower in candidate_skills_lower:
                preferred_bonus += 0.1
                if pref_skill not in matching_skills:
                    matching_skills.append(pref_skill)
        
        # Calculate final score
        required_score = total_score / len(required_skills) if required_skills else 1.0
        final_score = min(required_score + preferred_bonus, 1.0)
        
        return final_score, matching_skills, missing_skills
    
    def _find_related_skill_match(self, required_skill: str, candidate_skills: List[str]) -> float:
        """Find related skills that might satisfy the requirement"""
        required_lower = required_skill.lower()
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        
        # Check skill relationships
        if required_skill in self.skill_relationships:
            related_skills = [skill.lower() for skill in self.skill_relationships[required_skill]]
            for related in related_skills:
                if related in candidate_skills_lower:
                    return self.skill_weights['related_match']
        
        # Check reverse relationships
        for candidate_skill in candidate_skills:
            if candidate_skill in self.skill_relationships:
                related_skills = [skill.lower() for skill in self.skill_relationships[candidate_skill]]
                if required_lower in related_skills:
                    return self.skill_weights['related_match']
        
        # Check partial matches for compound skills
        if any(part in required_lower for part in candidate_skills_lower if len(part) > 3):
            return self.skill_weights['category_match']
        
        return 0.0
    
    def _calculate_experience_match(
        self, 
        candidate_years: int, 
        min_years: int, 
        max_years: int
    ) -> Tuple[float, str, int]:
        """Calculate experience match score"""
        
        if min_years is None:
            min_years = 0
        if max_years is None:
            max_years = 20
        
        gap = 0
        fit = ""
        
        if candidate_years < min_years:
            gap = min_years - candidate_years
            fit = "Under-qualified"
            # Penalize more heavily for significant gaps
            if gap <= 1:
                score = 0.8
            elif gap <= 2:
                score = 0.6
            else:
                score = max(0.2, 1.0 - (gap * 0.2))
        elif candidate_years > max_years:
            gap = candidate_years - max_years
            fit = "Over-qualified"
            # Slight penalty for being over-qualified
            if gap <= 2:
                score = 0.9
            elif gap <= 5:
                score = 0.8
            else:
                score = 0.7
        else:
            fit = "Perfect"
            score = 1.0
        
        return score, fit, gap
    
    def _calculate_location_match(
        self, 
        candidate_location: Optional[str], 
        job_location: Optional[str], 
        remote_ok: bool
    ) -> Tuple[float, bool]:
        """Calculate location compatibility score"""
        
        if remote_ok:
            return 1.0, True
        
        if not job_location or not candidate_location:
            return 0.7, True  # Neutral if location data is missing
        
        candidate_location = candidate_location.lower()
        job_location = job_location.lower()
        
        # Exact match
        if candidate_location == job_location:
            return 1.0, True
        
        # Same city/state match
        candidate_parts = candidate_location.split(',')
        job_parts = job_location.split(',')
        
        if len(candidate_parts) >= 2 and len(job_parts) >= 2:
            # Check state match
            if candidate_parts[-1].strip() == job_parts[-1].strip():
                return 0.8, True
            # Check city match
            if candidate_parts[0].strip() == job_parts[0].strip():
                return 0.9, True
        
        # Partial match
        if any(part.strip() in job_location for part in candidate_parts):
            return 0.6, True
        
        return 0.3, False
    
    def _calculate_education_match(
        self, 
        candidate_education: Optional[str], 
        job_education: Optional[str]
    ) -> float:
        """Calculate education match score"""
        
        if not job_education:
            return 1.0  # No requirement
        
        if not candidate_education:
            return 0.5  # Missing education data
        
        education_hierarchy = {
            'High School': 1,
            'Associates': 2,
            'Bachelors': 3,
            'Masters': 4,
            'PhD': 5
        }
        
        candidate_level = education_hierarchy.get(candidate_education, 0)
        
        # Parse job requirement
        job_req_level = 0
        job_education_lower = job_education.lower()
        
        if 'phd' in job_education_lower or 'doctorate' in job_education_lower:
            job_req_level = 5
        elif 'master' in job_education_lower:
            job_req_level = 4
        elif 'bachelor' in job_education_lower:
            job_req_level = 3
        elif 'associate' in job_education_lower:
            job_req_level = 2
        else:
            job_req_level = 1
        
        if candidate_level >= job_req_level:
            return 1.0
        elif candidate_level == job_req_level - 1:
            return 0.8
        else:
            return 0.5
    
    def _calculate_salary_match(
        self, 
        candidate_expectation: Optional[int], 
        job_min: Optional[int], 
        job_max: Optional[int]
    ) -> Tuple[float, bool]:
        """Calculate salary compatibility score"""
        
        if not candidate_expectation:
            return 1.0, True  # No expectation specified
        
        if not job_min and not job_max:
            return 1.0, True  # No salary range specified
        
        if job_min and job_max:
            if job_min <= candidate_expectation <= job_max:
                return 1.0, True
            elif candidate_expectation < job_min:
                # Candidate expects less - good for company
                return 1.0, True
            else:
                # Candidate expects more than budget
                gap_percent = (candidate_expectation - job_max) / job_max
                if gap_percent <= 0.1:  # Within 10%
                    return 0.8, True
                elif gap_percent <= 0.2:  # Within 20%
                    return 0.6, False
                else:
                    return 0.3, False
        
        return 0.7, True
    
    def _generate_recommendation(
        self,
        overall_score: float,
        skill_score: float,
        experience_score: float,
        location_score: float,
        matching_skills: List[str],
        missing_skills: List[str],
        experience_fit: str
    ) -> Tuple[str, List[str], List[str]]:
        """Generate recommendation and reasons"""
        
        reasons = []
        concerns = []
        
        # Analyze strengths
        if skill_score >= 0.8:
            reasons.append("Strong technical skill alignment")
        elif skill_score >= 0.6:
            reasons.append("Good skill match with some gaps")
        
        if experience_score >= 0.9:
            reasons.append(f"Perfect experience level ({experience_fit})")
        elif experience_score >= 0.7:
            reasons.append("Appropriate experience level")
        
        if location_score >= 0.9:
            reasons.append("Excellent location match")
        
        if len(matching_skills) > 5:
            reasons.append("Extensive relevant skill set")
        
        # Analyze concerns
        if skill_score < 0.6:
            concerns.append("Significant skill gaps identified")
        
        if missing_skills:
            if len(missing_skills) == 1:
                concerns.append(f"Missing required skill: {missing_skills[0]}")
            elif len(missing_skills) <= 3:
                concerns.append(f"Missing skills: {', '.join(missing_skills)}")
            else:
                concerns.append(f"Missing {len(missing_skills)} required skills")
        
        if experience_fit == "Under-qualified":
            concerns.append("Below minimum experience requirement")
        elif experience_fit == "Over-qualified":
            concerns.append("May be over-qualified for the role")
        
        if location_score < 0.5:
            concerns.append("Location mismatch - may require relocation")
        
        # Generate overall recommendation
        if overall_score >= 0.85:
            recommendation = "Excellent Match"
        elif overall_score >= 0.75:
            recommendation = "Strong Match"
        elif overall_score >= 0.65:
            recommendation = "Good Match"
        elif overall_score >= 0.5:
            recommendation = "Potential Match"
        else:
            recommendation = "Poor Match"
        
        return recommendation, reasons, concerns
