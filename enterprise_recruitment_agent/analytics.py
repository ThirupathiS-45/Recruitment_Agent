"""
Analytics Engine for Enterprise Recruitment Agent

Provides comprehensive analytics, reporting, and insights for recruitment operations.
Optimized for large datasets with advanced metrics and visualizations.
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from models import CandidateProfile, JobPosting, MatchResult
from database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Advanced analytics engine for recruitment insights"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def generate_dashboard(
        self,
        date_range: str = "30d",
        job_id: Optional[int] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive recruitment dashboard"""
        
        logger.info(f"Generating analytics dashboard for range: {date_range}")
        
        # Parse date range
        start_date, end_date = self._parse_date_range(date_range)
        
        # Gather all analytics data
        dashboard_data = {}
        
        # Core metrics
        dashboard_data.update(await self._get_core_metrics(start_date, end_date, job_id, department))
        
        # Performance metrics
        dashboard_data.update(await self._get_performance_metrics(start_date, end_date, job_id, department))
        
        # Skill analytics
        dashboard_data.update(await self._get_skill_analytics(start_date, end_date, department))
        
        # Source analytics
        dashboard_data.update(await self._get_source_analytics(start_date, end_date))
        
        # Trends and patterns
        dashboard_data.update(await self._get_trend_analytics(start_date, end_date, department))
        
        # Recent activity
        dashboard_data['recent_activity'] = await self._get_recent_activity(limit=10)
        
        logger.info("Dashboard generation completed")
        return dashboard_data
    
    async def generate_job_report(
        self,
        job_id: int,
        include_analytics: bool = True,
        include_candidates: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive report for a specific job"""
        
        logger.info(f"Generating job report for job ID: {job_id}")
        
        async with self.db_manager.get_connection() as conn:
            # Get job details
            job_query = """
                SELECT * FROM job_postings WHERE id = $1
            """
            job_row = await conn.fetchrow(job_query, job_id)
            
            if not job_row:
                raise ValueError(f"Job {job_id} not found")
            
            job_data = dict(job_row)
            
            # Parse JSON fields
            job_data['required_skills'] = json.loads(job_data.get('required_skills') or '[]')
            job_data['preferred_skills'] = json.loads(job_data.get('preferred_skills') or '[]')
            job_data['certifications'] = json.loads(job_data.get('certifications') or '[]')
            
            report = {
                'job_id': job_id,
                'job_title': job_data['title'],
                'company': job_data['company'],
                'department': job_data.get('department'),
                'location': job_data.get('location'),
                'posted_date': job_data.get('posted_date'),
                'status': job_data.get('status'),
                'required_skills': job_data['required_skills'],
                'preferred_skills': job_data['preferred_skills']
            }
            
            # Application statistics
            app_stats = await self._get_job_application_stats(conn, job_id)
            report.update(app_stats)
            
            if include_analytics:
                # Performance metrics
                performance = await self._get_job_performance_metrics(conn, job_id)
                report.update(performance)
                
                # Skills analysis
                skills_analysis = await self._get_job_skills_analysis(conn, job_id)
                report.update(skills_analysis)
            
            if include_candidates:
                # Top candidates
                top_candidates = await self._get_job_top_candidates(conn, job_id, limit=10)
                report['top_candidates'] = top_candidates
            
            # Recommendations
            report['recommendations'] = await self._generate_job_recommendations(report)
            
            return report
    
    async def _get_core_metrics(
        self,
        start_date: date,
        end_date: date,
        job_id: Optional[int],
        department: Optional[str]
    ) -> Dict[str, Any]:
        """Get core recruitment metrics"""
        
        async with self.db_manager.get_connection() as conn:
            metrics = {}
            
            # Build base filters
            date_filter = "WHERE created_at >= $1 AND created_at <= $2"
            params = [start_date, end_date]
            
            # Total candidates
            query = f"SELECT COUNT(*) FROM candidates {date_filter}"
            metrics['total_candidates'] = await conn.fetchval(query, *params)
            
            # Active jobs
            job_filter = "WHERE status = 'Open'"
            if department:
                job_filter += " AND department = $1"
                job_params = [department]
            else:
                job_params = []
            
            query = f"SELECT COUNT(*) FROM job_postings {job_filter}"
            metrics['active_jobs'] = await conn.fetchval(query, *job_params)
            
            # Total applications
            app_filter = date_filter.replace("created_at", "application_date")
            query = f"SELECT COUNT(*) FROM applications {app_filter}"
            metrics['total_applications'] = await conn.fetchval(query, *params)
            
            # Scheduled interviews
            interview_filter = "WHERE scheduled_date >= $1 AND scheduled_date <= $2 AND status = 'Scheduled'"
            query = f"SELECT COUNT(*) FROM interviews {interview_filter}"
            metrics['interviews_scheduled'] = await conn.fetchval(query, *params)
            
            # Hiring metrics
            hire_filter = "WHERE decision = 'Hired' AND decision_date >= $1 AND decision_date <= $2"
            query = f"SELECT COUNT(*) FROM applications {hire_filter}"
            hires = await conn.fetchval(query, *params)
            
            decision_filter = "WHERE decision IS NOT NULL AND decision_date >= $1 AND decision_date <= $2"
            query = f"SELECT COUNT(*) FROM applications {decision_filter}"
            total_decisions = await conn.fetchval(query, *params)
            
            metrics['hires'] = hires
            metrics['hiring_rate'] = hires / total_decisions if total_decisions > 0 else 0
            
            return metrics
    
    async def _get_performance_metrics(
        self,
        start_date: date,
        end_date: date,
        job_id: Optional[int],
        department: Optional[str]
    ) -> Dict[str, Any]:
        """Get performance and efficiency metrics"""
        
        async with self.db_manager.get_connection() as conn:
            metrics = {}
            
            # Average time to hire
            time_to_hire_query = """
                SELECT AVG(EXTRACT(DAY FROM (decision_date - application_date))) as avg_days
                FROM applications 
                WHERE decision = 'Hired' 
                AND decision_date >= $1 AND decision_date <= $2
            """
            
            avg_time_to_hire = await conn.fetchval(time_to_hire_query, start_date, end_date)
            metrics['avg_time_to_hire'] = round(avg_time_to_hire or 0, 1)
            
            # Average time to interview
            time_to_interview_query = """
                SELECT AVG(EXTRACT(DAY FROM (i.scheduled_date - a.application_date))) as avg_days
                FROM applications a
                JOIN interviews i ON a.id = i.application_id
                WHERE a.application_date >= $1 AND a.application_date <= $2
                AND i.status = 'Scheduled'
            """
            
            avg_time_to_interview = await conn.fetchval(time_to_interview_query, start_date, end_date)
            metrics['avg_time_to_interview'] = round(avg_time_to_interview or 0, 1)
            
            # Conversion rates
            conversion_query = """
                SELECT 
                    COUNT(CASE WHEN status = 'Applied' THEN 1 END) as applied,
                    COUNT(CASE WHEN status IN ('Phone Screen', 'Technical Interview', 'Final Interview') THEN 1 END) as interviewed,
                    COUNT(CASE WHEN decision = 'Hired' THEN 1 END) as hired
                FROM applications 
                WHERE application_date >= $1 AND application_date <= $2
            """
            
            conversion_data = await conn.fetchrow(conversion_query, start_date, end_date)
            
            if conversion_data:
                applied = conversion_data['applied'] or 0
                interviewed = conversion_data['interviewed'] or 0
                hired = conversion_data['hired'] or 0
                
                metrics['interview_rate'] = interviewed / applied if applied > 0 else 0
                metrics['hire_rate'] = hired / applied if applied > 0 else 0
                metrics['interview_to_hire_rate'] = hired / interviewed if interviewed > 0 else 0
            
            # Quality metrics
            quality_query = """
                SELECT 
                    AVG(overall_score) as avg_candidate_score,
                    AVG(final_score) as avg_final_score
                FROM applications a
                JOIN candidates c ON a.candidate_id = c.id
                WHERE a.application_date >= $1 AND a.application_date <= $2
            """
            
            quality_data = await conn.fetchrow(quality_query, start_date, end_date)
            
            if quality_data:
                metrics['avg_candidate_quality'] = round(quality_data['avg_candidate_score'] or 0, 2)
                metrics['avg_final_score'] = round(quality_data['avg_final_score'] or 0, 2)
            
            return metrics
    
    async def _get_skill_analytics(
        self,
        start_date: date,
        end_date: date,
        department: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze skill demand and supply"""
        
        async with self.db_manager.get_connection() as conn:
            # Most demanded skills (from job postings)
            demand_query = """
                SELECT 
                    skill,
                    COUNT(*) as demand_count,
                    AVG(salary_max) as avg_salary
                FROM (
                    SELECT 
                        unnest(required_skills::text[]) as skill,
                        salary_max
                    FROM job_postings 
                    WHERE status = 'Open'
                    AND ($1::text IS NULL OR department = $1)
                ) skills_demand
                GROUP BY skill
                ORDER BY demand_count DESC
                LIMIT 15
            """
            
            demand_rows = await conn.fetch(demand_query, department)
            top_skills = []
            
            for row in demand_rows:
                top_skills.append({
                    'name': row['skill'],
                    'demand': row['demand_count'],
                    'avg_salary': round(row['avg_salary'] or 0, 0)
                })
            
            # Most common skills (from candidates)
            supply_query = """
                SELECT 
                    skill,
                    COUNT(*) as candidate_count,
                    AVG(c.overall_score) as avg_score
                FROM (
                    SELECT 
                        unnest(skills::text[]) as skill,
                        overall_score
                    FROM candidates c
                    WHERE created_at >= $1 AND created_at <= $2
                ) skills_supply s
                JOIN candidates c ON true
                GROUP BY skill
                ORDER BY candidate_count DESC
                LIMIT 15
            """
            
            supply_rows = await conn.fetch(supply_query, start_date, end_date)
            common_skills = []
            
            for row in supply_rows:
                common_skills.append({
                    'name': row['skill'],
                    'candidates': row['candidate_count'],
                    'avg_score': round(row['avg_score'] or 0, 2)
                })
            
            # Skill gaps (high demand, low supply)
            skill_gaps = []
            demand_skills = {skill['name']: skill['demand'] for skill in top_skills}
            supply_skills = {skill['name']: skill['candidates'] for skill in common_skills}
            
            for skill_name, demand in demand_skills.items():
                supply = supply_skills.get(skill_name, 0)
                if demand > 0:
                    gap_ratio = demand / max(supply, 1)
                    if gap_ratio > 2:  # High demand, low supply
                        skill_gaps.append({
                            'skill': skill_name,
                            'demand': demand,
                            'supply': supply,
                            'gap_ratio': round(gap_ratio, 2)
                        })
            
            skill_gaps.sort(key=lambda x: x['gap_ratio'], reverse=True)
            
            return {
                'top_skills': top_skills,
                'common_skills': common_skills,
                'skill_gaps': skill_gaps[:10],
                'missing_skills': [gap['skill'] for gap in skill_gaps[:5]]
            }
    
    async def _get_source_analytics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Analyze candidate sources and their performance"""
        
        async with self.db_manager.get_connection() as conn:
            source_query = """
                SELECT 
                    c.source,
                    COUNT(*) as candidate_count,
                    COUNT(a.id) as application_count,
                    COUNT(CASE WHEN a.decision = 'Hired' THEN 1 END) as hire_count,
                    AVG(c.overall_score) as avg_quality_score,
                    AVG(EXTRACT(DAY FROM (a.decision_date - a.application_date))) as avg_time_to_decision
                FROM candidates c
                LEFT JOIN applications a ON c.id = a.candidate_id
                WHERE c.created_at >= $1 AND c.created_at <= $2
                AND c.source IS NOT NULL
                GROUP BY c.source
                ORDER BY candidate_count DESC
            """
            
            source_rows = await conn.fetch(source_query, start_date, end_date)
            
            top_sources = []
            for row in source_rows:
                hire_rate = (row['hire_count'] or 0) / max(row['application_count'] or 1, 1)
                quality_score = row['avg_quality_score'] or 0
                
                top_sources.append({
                    'name': row['source'] or 'Unknown',
                    'candidates': row['candidate_count'],
                    'applications': row['application_count'] or 0,
                    'hires': row['hire_count'] or 0,
                    'hire_rate': round(hire_rate * 100, 1),
                    'quality_score': round(quality_score, 1),
                    'avg_time_to_decision': round(row['avg_time_to_decision'] or 0, 1)
                })
            
            return {'top_sources': top_sources}
    
    async def _get_trend_analytics(
        self,
        start_date: date,
        end_date: date,
        department: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze trends over time"""
        
        async with self.db_manager.get_connection() as conn:
            
            # Weekly application trends
            trend_query = """
                SELECT 
                    DATE_TRUNC('week', application_date) as week,
                    COUNT(*) as applications,
                    COUNT(CASE WHEN decision = 'Hired' THEN 1 END) as hires
                FROM applications
                WHERE application_date >= $1 AND application_date <= $2
                GROUP BY week
                ORDER BY week
            """
            
            trend_rows = await conn.fetch(trend_query, start_date, end_date)
            
            weekly_trends = []
            for row in trend_rows:
                weekly_trends.append({
                    'week': row['week'].strftime('%Y-%m-%d'),
                    'applications': row['applications'],
                    'hires': row['hires'],
                    'hire_rate': round((row['hires'] / max(row['applications'], 1)) * 100, 1)
                })
            
            # Department performance (if not filtering by department)
            if not department:
                dept_query = """
                    SELECT 
                        j.department,
                        COUNT(a.id) as applications,
                        COUNT(CASE WHEN a.decision = 'Hired' THEN 1 END) as hires,
                        AVG(EXTRACT(DAY FROM (a.decision_date - a.application_date))) as avg_time_to_hire
                    FROM applications a
                    JOIN job_postings j ON a.job_id = j.id
                    WHERE a.application_date >= $1 AND a.application_date <= $2
                    AND j.department IS NOT NULL
                    GROUP BY j.department
                    ORDER BY applications DESC
                """
                
                dept_rows = await conn.fetch(dept_query, start_date, end_date)
                
                department_stats = []
                for row in dept_rows:
                    hire_rate = (row['hires'] / max(row['applications'], 1)) * 100
                    
                    department_stats.append({
                        'name': row['department'],
                        'applications': row['applications'],
                        'hires': row['hires'],
                        'hire_rate': round(hire_rate, 1),
                        'avg_time_to_hire': round(row['avg_time_to_hire'] or 0, 1)
                    })
            else:
                department_stats = []
            
            return {
                'weekly_trends': weekly_trends,
                'department_stats': department_stats
            }
    
    async def _get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent recruitment activity"""
        
        async with self.db_manager.get_connection() as conn:
            activity_query = """
                SELECT 
                    'Application' as type,
                    a.application_date as timestamp,
                    c.name as candidate_name,
                    j.title as job_title,
                    j.company,
                    a.status
                FROM applications a
                JOIN candidates c ON a.candidate_id = c.id
                JOIN job_postings j ON a.job_id = j.id
                ORDER BY a.application_date DESC
                LIMIT $1
            """
            
            activity_rows = await conn.fetch(activity_query, limit)
            
            activities = []
            for row in activity_rows:
                activities.append({
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'type': row['type'],
                    'description': f"{row['candidate_name']} applied for {row['job_title']} at {row['company']}",
                    'status': row['status']
                })
            
            return activities
    
    async def _get_job_application_stats(self, conn, job_id: int) -> Dict[str, Any]:
        """Get application statistics for a specific job"""
        
        stats_query = """
            SELECT 
                COUNT(*) as total_applications,
                COUNT(CASE WHEN status IN ('Phone Screen', 'Technical Interview', 'Final Interview') THEN 1 END) as qualified_candidates,
                COUNT(CASE WHEN status = 'Interview Scheduled' THEN 1 END) as interviews_scheduled,
                COUNT(CASE WHEN status = 'Offer Pending' THEN 1 END) as offers_made,
                COUNT(CASE WHEN decision = 'Hired' THEN 1 END) as hires
            FROM applications
            WHERE job_id = $1
        """
        
        stats_row = await conn.fetchrow(stats_query, job_id)
        
        return {
            'total_applications': stats_row['total_applications'],
            'qualified_candidates': stats_row['qualified_candidates'],
            'interviews_scheduled': stats_row['interviews_scheduled'],
            'offers_made': stats_row['offers_made'],
            'hires': stats_row['hires']
        }
    
    async def _get_job_performance_metrics(self, conn, job_id: int) -> Dict[str, Any]:
        """Get performance metrics for a specific job"""
        
        performance_query = """
            SELECT 
                AVG(EXTRACT(DAY FROM (i.scheduled_date - a.application_date))) as avg_time_to_interview,
                AVG(EXTRACT(DAY FROM (a.decision_date - a.application_date))) as avg_time_to_hire,
                AVG(a.initial_score) as avg_initial_score,
                AVG(a.final_score) as avg_final_score
            FROM applications a
            LEFT JOIN interviews i ON a.id = i.application_id
            WHERE a.job_id = $1
        """
        
        perf_row = await conn.fetchrow(performance_query, job_id)
        
        # Calculate conversion rate
        conversion_query = """
            SELECT 
                COUNT(*) as total_apps,
                COUNT(CASE WHEN decision = 'Hired' THEN 1 END) as hires
            FROM applications
            WHERE job_id = $1
        """
        
        conv_row = await conn.fetchrow(conversion_query, job_id)
        
        conversion_rate = 0
        if conv_row and conv_row['total_apps'] > 0:
            conversion_rate = conv_row['hires'] / conv_row['total_apps']
        
        return {
            'avg_time_to_interview': round(perf_row['avg_time_to_interview'] or 0, 1),
            'avg_time_to_hire': round(perf_row['avg_time_to_hire'] or 0, 1),
            'quality_score': round(perf_row['avg_initial_score'] or 0, 1),
            'final_quality_score': round(perf_row['avg_final_score'] or 0, 1),
            'conversion_rate': round(conversion_rate * 100, 1)
        }
    
    async def _get_job_skills_analysis(self, conn, job_id: int) -> Dict[str, Any]:
        """Analyze skills for a specific job"""
        
        skills_query = """
            SELECT 
                unnest(c.skills::text[]) as skill,
                COUNT(*) as candidate_count,
                AVG(c.overall_score) as avg_score
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.job_id = $1
            GROUP BY skill
            ORDER BY candidate_count DESC
            LIMIT 10
        """
        
        skills_rows = await conn.fetch(skills_query, job_id)
        
        common_skills = []
        for row in skills_rows:
            common_skills.append(row['skill'])
        
        # Get required skills that are missing
        job_query = """
            SELECT required_skills, preferred_skills
            FROM job_postings
            WHERE id = $1
        """
        
        job_row = await conn.fetchrow(job_query, job_id)
        
        if job_row:
            required_skills = json.loads(job_row['required_skills'] or '[]')
            missing_skills = [skill for skill in required_skills if skill not in common_skills]
        else:
            missing_skills = []
        
        return {
            'common_skills': common_skills,
            'missing_skills': missing_skills
        }
    
    async def _get_job_top_candidates(self, conn, job_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top candidates for a specific job"""
        
        candidates_query = """
            SELECT 
                c.id,
                c.name,
                c.email,
                c.overall_score,
                m.overall_match_score,
                a.status
            FROM candidates c
            LEFT JOIN match_results m ON c.id = m.candidate_id AND m.job_id = $1
            LEFT JOIN applications a ON c.id = a.candidate_id AND a.job_id = $1
            WHERE m.job_id = $1
            ORDER BY m.overall_match_score DESC
            LIMIT $2
        """
        
        candidate_rows = await conn.fetch(candidates_query, job_id, limit)
        
        top_candidates = []
        for row in candidate_rows:
            top_candidates.append({
                'id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'overall_score': round(row['overall_score'] or 0, 2),
                'match_score': round(row['overall_match_score'] or 0, 2),
                'status': row['status'] or 'Not Applied'
            })
        
        return top_candidates
    
    async def _generate_job_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations for job improvement"""
        
        recommendations = []
        
        # Application volume recommendations
        if report.get('total_applications', 0) < 10:
            recommendations.append("Consider expanding job posting to more platforms to increase application volume")
        
        # Conversion rate recommendations
        conversion_rate = report.get('conversion_rate', 0)
        if conversion_rate < 5:
            recommendations.append("Low conversion rate - review job requirements and application process")
        elif conversion_rate > 20:
            recommendations.append("High conversion rate - job requirements may be too broad")
        
        # Time to hire recommendations
        time_to_hire = report.get('avg_time_to_hire', 0)
        if time_to_hire > 30:
            recommendations.append("Consider streamlining the interview process to reduce time to hire")
        
        # Skill gap recommendations
        missing_skills = report.get('missing_skills', [])
        if missing_skills:
            recommendations.append(f"Consider adjusting requirements for: {', '.join(missing_skills[:3])}")
        
        # Quality recommendations
        quality_score = report.get('quality_score', 0)
        if quality_score < 60:
            recommendations.append("Low candidate quality - review sourcing channels and job description")
        
        return recommendations
    
    def _parse_date_range(self, date_range: str) -> Tuple[date, date]:
        """Parse date range string into start and end dates"""
        
        end_date = date.today()
        
        if date_range.endswith('d'):
            days = int(date_range[:-1])
            start_date = end_date - timedelta(days=days)
        elif date_range.endswith('w'):
            weeks = int(date_range[:-1])
            start_date = end_date - timedelta(weeks=weeks)
        elif date_range.endswith('m'):
            months = int(date_range[:-1])
            start_date = end_date - timedelta(days=months * 30)
        else:
            # Default to 30 days
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
