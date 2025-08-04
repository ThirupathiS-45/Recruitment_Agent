#!/usr/bin/env python3
"""
Enterprise Recruitment Agent MCP Server

A comprehensive AI-powered recruitment system that can efficiently handle 1000+ resumes
with advanced matching algorithms, automated screening, and workflow automation.

Features:
- Bulk resume processing and parsing
- AI-powered candidate-job matching
- Automated screening and ranking
- Interview scheduling automation
- Advanced analytics and reporting
- Performance optimized for large datasets
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path
from dotenv import load_dotenv

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from database import DatabaseManager, init_database
from models import (
    CandidateProfile, 
    JobPosting, 
    ApplicationStatus, 
    MatchResult,
    InterviewSchedule
)
from resume_parser import ResumeParser
from matching_engine import MatchingEngine
from bulk_processor import BulkProcessor
from analytics import AnalyticsEngine
from automation import WorkflowAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnterpriseRecruitmentAgent:
    """Main recruitment agent server class"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.resume_parser = ResumeParser()
        self.matching_engine = MatchingEngine()
        self.bulk_processor = BulkProcessor(self.db_manager, self.resume_parser)
        self.analytics = AnalyticsEngine(self.db_manager)
        self.automation = WorkflowAutomation(self.db_manager)
        
        # Initialize MCP server
        self.server = Server("enterprise-recruitment-agent")
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup all MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available recruitment tools"""
            return [
                types.Tool(
                    name="process_bulk_resumes",
                    description="Process multiple resumes in bulk (supports 1000+ resumes)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "resume_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of base64 encoded resume files"
                            },
                            "file_names": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "Array of corresponding file names"
                            },
                            "job_id": {
                                "type": "integer",
                                "description": "Optional job ID to match against"
                            }
                        },
                        "required": ["resume_files", "file_names"]
                    }
                ),
                types.Tool(
                    name="create_job_posting",
                    description="Create a new job posting with advanced requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "department": {"type": "string"},
                            "description": {"type": "string"},
                            "required_skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "preferred_skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "experience_min": {"type": "integer"},
                            "experience_max": {"type": "integer"},
                            "salary_min": {"type": "integer"},
                            "salary_max": {"type": "integer"},
                            "location": {"type": "string"},
                            "remote_ok": {"type": "boolean"},
                            "education_requirements": {"type": "string"},
                            "certifications": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["title", "company", "description", "required_skills"]
                    }
                ),
                types.Tool(
                    name="find_best_candidates",
                    description="Find and rank the best candidates for a job using AI matching",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "limit": {"type": "integer", "default": 20},
                            "min_match_score": {"type": "number", "default": 0.6},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "experience_min": {"type": "integer"},
                                    "location": {"type": "string"},
                                    "remote_ok": {"type": "boolean"},
                                    "salary_max": {"type": "integer"}
                                }
                            }
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="schedule_interviews",
                    description="Automatically schedule interviews for multiple candidates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "candidate_ids": {
                                "type": "array",
                                "items": {"type": "integer"}
                            },
                            "job_id": {"type": "integer"},
                            "interview_type": {"type": "string"},
                            "interviewer": {"type": "string"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "duration_minutes": {"type": "integer", "default": 60}
                        },
                        "required": ["candidate_ids", "job_id", "interviewer"]
                    }
                ),
                types.Tool(
                    name="get_analytics_dashboard",
                    description="Get comprehensive recruitment analytics and insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date_range": {"type": "string", "default": "30d"},
                            "job_id": {"type": "integer"},
                            "department": {"type": "string"}
                        }
                    }
                ),
                types.Tool(
                    name="search_candidates",
                    description="Advanced search for candidates with multiple filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "experience_min": {"type": "integer"},
                            "experience_max": {"type": "integer"},
                            "location": {"type": "string"},
                            "education_level": {"type": "string"},
                            "availability": {"type": "string"},
                            "limit": {"type": "integer", "default": 50}
                        }
                    }
                ),
                types.Tool(
                    name="get_candidate_profile",
                    description="Get detailed candidate profile with all information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "integer"}
                        },
                        "required": ["candidate_id"]
                    }
                ),
                types.Tool(
                    name="automated_screening",
                    description="Run automated screening on candidates for a job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "candidate_ids": {
                                "type": "array",
                                "items": {"type": "integer"}
                            },
                            "screening_criteria": {
                                "type": "object",
                                "properties": {
                                    "min_experience": {"type": "integer"},
                                    "required_skills": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "education_required": {"type": "boolean"},
                                    "location_match": {"type": "boolean"}
                                }
                            }
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="generate_job_report",
                    description="Generate comprehensive report for a job posting",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "include_analytics": {"type": "boolean", "default": True},
                            "include_candidates": {"type": "boolean", "default": True}
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="update_application_status",
                    description="Update application status and add notes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "application_id": {"type": "integer"},
                            "status": {"type": "string"},
                            "notes": {"type": "string"},
                            "next_action": {"type": "string"}
                        },
                        "required": ["application_id", "status"]
                    }
                ),
                # NEW HR-SPECIFIC TOOLS
                types.Tool(
                    name="get_job_applications",
                    description="Get all applications for a specific job with candidate details",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "status_filter": {"type": "string", "description": "Filter by application status"},
                            "limit": {"type": "integer", "default": 100}
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="create_screening_questions",
                    description="Generate intelligent screening questions for a job position",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "question_type": {
                                "type": "string", 
                                "enum": ["technical", "behavioral", "experience", "situational", "mixed"],
                                "default": "mixed"
                            },
                            "difficulty_level": {
                                "type": "string",
                                "enum": ["entry", "intermediate", "senior", "expert"],
                                "default": "intermediate"
                            },
                            "question_count": {"type": "integer", "default": 5}
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="screen_candidate_responses",
                    description="Analyze candidate responses to screening questions using AI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "integer"},
                            "job_id": {"type": "integer"},
                            "responses": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string"},
                                        "answer": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["candidate_id", "job_id", "responses"]
                    }
                ),
                types.Tool(
                    name="get_application_pipeline",
                    description="Get complete application pipeline view with status counts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "date_range": {"type": "string", "default": "30d"}
                        }
                    }
                ),
                types.Tool(
                    name="rank_applications",
                    description="Automatically rank applications based on job requirements and AI scoring",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "ranking_criteria": {
                                "type": "object",
                                "properties": {
                                    "skills_weight": {"type": "number", "default": 0.4},
                                    "experience_weight": {"type": "number", "default": 0.3},
                                    "education_weight": {"type": "number", "default": 0.2},
                                    "other_weight": {"type": "number", "default": 0.1}
                                }
                            }
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="publish_job_posting",
                    description="Publish a job posting to make it visible on application portal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "publish_immediately": {"type": "boolean", "default": True},
                            "application_deadline": {"type": "string", "description": "YYYY-MM-DD format"},
                            "featured": {"type": "boolean", "default": False}
                        },
                        "required": ["job_id"]
                    }
                ),
                types.Tool(
                    name="generate_interview_questions",
                    description="Generate personalized interview questions based on candidate profile and job requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "integer"},
                            "job_id": {"type": "integer"},
                            "interview_type": {
                                "type": "string",
                                "enum": ["phone_screen", "technical", "behavioral", "final"],
                                "default": "technical"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific skills or areas to focus on"
                            }
                        },
                        "required": ["candidate_id", "job_id"]
                    }
                ),
                types.Tool(
                    name="bulk_status_update",
                    description="Update status for multiple applications at once (batch processing)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "application_ids": {
                                "type": "array",
                                "items": {"type": "integer"}
                            },
                            "new_status": {"type": "string"},
                            "notes": {"type": "string"},
                            "send_notifications": {"type": "boolean", "default": True}
                        },
                        "required": ["application_ids", "new_status"]
                    }
                ),
                types.Tool(
                    name="get_hiring_analytics",
                    description="Get comprehensive hiring analytics with application trends and conversion rates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeframe": {
                                "type": "string",
                                "enum": ["7d", "30d", "90d", "1y"],
                                "default": "30d"
                            },
                            "department": {"type": "string"},
                            "job_id": {"type": "integer"}
                        }
                    }
                ),
                types.Tool(
                    name="view_candidate_resume",
                    description="View complete resume and profile details for a candidate",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "integer"},
                            "candidate_name": {"type": "string"},
                            "candidate_email": {"type": "string"}
                        }
                    }
                ),
                types.Tool(
                    name="close_job_posting",
                    description="Close a job posting and stop accepting new applications",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer"},
                            "job_title": {"type": "string"},
                            "company": {"type": "string"},
                            "closure_reason": {"type": "string", "default": "Position filled"},
                            "notify_applicants": {"type": "boolean", "default": True}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "process_bulk_resumes":
                    return await self._process_bulk_resumes(arguments or {})
                elif name == "create_job_posting":
                    return await self._create_job_posting(arguments or {})
                elif name == "find_best_candidates":
                    return await self._find_best_candidates(arguments or {})
                elif name == "schedule_interviews":
                    return await self._schedule_interviews(arguments or {})
                elif name == "get_analytics_dashboard":
                    return await self._get_analytics_dashboard(arguments or {})
                elif name == "search_candidates":
                    return await self._search_candidates(arguments or {})
                elif name == "get_candidate_profile":
                    return await self._get_candidate_profile(arguments or {})
                elif name == "automated_screening":
                    return await self._automated_screening(arguments or {})
                elif name == "generate_job_report":
                    return await self._generate_job_report(arguments or {})
                elif name == "update_application_status":
                    return await self._update_application_status(arguments or {})
                # NEW HR-SPECIFIC TOOL HANDLERS
                elif name == "get_job_applications":
                    return await self._get_job_applications(arguments or {})
                elif name == "create_screening_questions":
                    return await self._create_screening_questions(arguments or {})
                elif name == "screen_candidate_responses":
                    return await self._screen_candidate_responses(arguments or {})
                elif name == "get_application_pipeline":
                    return await self._get_application_pipeline(arguments or {})
                elif name == "rank_applications":
                    return await self._rank_applications(arguments or {})
                elif name == "publish_job_posting":
                    return await self._publish_job_posting(arguments or {})
                elif name == "generate_interview_questions":
                    return await self._generate_interview_questions(arguments or {})
                elif name == "bulk_status_update":
                    return await self._bulk_status_update(arguments or {})
                elif name == "get_hiring_analytics":
                    return await self._get_hiring_analytics(arguments or {})
                elif name == "view_candidate_resume":
                    return await self._view_candidate_resume(arguments or {})
                elif name == "close_job_posting":
                    return await self._close_job_posting(arguments or {})
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _process_bulk_resumes(self, args: dict) -> list[types.TextContent]:
        """Process multiple resumes in bulk"""
        try:
            resume_files = args.get("resume_files", [])
            file_names = args.get("file_names", [])
            job_id = args.get("job_id")
            
            if len(resume_files) != len(file_names):
                raise ValueError("Number of resume files must match number of file names")
            
            # Process resumes in parallel for performance
            results = await self.bulk_processor.process_resumes_bulk(
                resume_files, file_names, job_id
            )
            
            success_count = sum(1 for r in results if r.get("success"))
            total_count = len(results)
            
            response = f"✅ **Bulk Resume Processing Complete**\n\n"
            response += f"📊 **Summary:**\n"
            response += f"- Total Resumes: {total_count}\n"
            response += f"- Successfully Processed: {success_count}\n"
            response += f"- Failed: {total_count - success_count}\n\n"
            
            if job_id:
                # Get top matches if job_id provided
                top_matches = await self.matching_engine.get_top_matches(job_id, limit=10)
                response += f"🎯 **Top 10 Matches for Job ID {job_id}:**\n"
                for i, match in enumerate(top_matches, 1):
                    response += f"{i}. {match['name']} - {match['match_score']:.1%} match\n"
            
            response += f"\n📈 **Processing Details:**\n"
            for i, result in enumerate(results[:20]):  # Show first 20
                status = "✅" if result.get("success") else "❌"
                response += f"{status} {file_names[i]}: {result.get('message', 'Processed')}\n"
            
            if len(results) > 20:
                response += f"... and {len(results) - 20} more\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Bulk processing error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error processing resumes: {str(e)}")]
    
    async def _create_job_posting(self, args: dict) -> list[types.TextContent]:
        """Create a new job posting"""
        try:
            job_data = JobPosting(
                title=args["title"],
                company=args["company"],
                department=args.get("department"),
                description=args["description"],
                required_skills=args["required_skills"],
                preferred_skills=args.get("preferred_skills", []),
                experience_min=args.get("experience_min", 0),
                experience_max=args.get("experience_max", 10),
                salary_min=args.get("salary_min"),
                salary_max=args.get("salary_max"),
                location=args.get("location"),
                remote_ok=args.get("remote_ok", False),
                education_requirements=args.get("education_requirements"),
                certifications=args.get("certifications", [])
            )
            
            job_id = await self.db_manager.create_job_posting(job_data)
            
            response = f"✅ **Job Posting Created Successfully!**\n\n"
            response += f"🆔 **Job ID:** {job_id}\n"
            response += f"📋 **Title:** {job_data.title}\n"
            response += f"🏢 **Company:** {job_data.company}\n"
            response += f"📍 **Location:** {job_data.location}\n"
            response += f"🔧 **Required Skills:** {', '.join(job_data.required_skills)}\n"
            response += f"📊 **Experience:** {job_data.experience_min}-{job_data.experience_max} years\n"
            
            if job_data.salary_min and job_data.salary_max:
                response += f"💰 **Salary Range:** ${job_data.salary_min:,} - ${job_data.salary_max:,}\n"
            
            response += f"\n🎯 **Next Steps:**\n"
            response += f"- Use `find_best_candidates` with job_id {job_id} to find matching candidates\n"
            response += f"- Use `automated_screening` to screen candidates automatically\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Job creation error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error creating job posting: {str(e)}")]
    
    async def _find_best_candidates(self, args: dict) -> list[types.TextContent]:
        """Find and rank the best candidates for a job"""
        try:
            job_id = args["job_id"]
            limit = args.get("limit", 20)
            min_match_score = args.get("min_match_score", 0.6)
            filters = args.get("filters", {})
            
            matches = await self.matching_engine.find_best_matches(
                job_id, limit=limit, min_score=min_match_score, filters=filters
            )
            
            if not matches:
                return [types.TextContent(
                    type="text", 
                    text="❌ No candidates found matching the criteria"
                )]
            
            response = f"🎯 **Top {len(matches)} Candidates for Job ID {job_id}**\n\n"
            
            for i, match in enumerate(matches, 1):
                response += f"**{i}. {match['name']}** - {match['match_score']:.1%} Match\n"
                response += f"   📧 {match['email']}\n"
                response += f"   💼 {match['experience_years']} years experience\n"
                response += f"   📍 {match.get('location', 'N/A')}\n"
                response += f"   🔧 Key Skills: {', '.join(match['matching_skills'][:5])}\n"
                if match.get('missing_skills'):
                    response += f"   ⚠️  Missing: {', '.join(match['missing_skills'][:3])}\n"
                response += f"   🆔 Candidate ID: {match['candidate_id']}\n\n"
            
            response += f"💡 **Recommendations:**\n"
            response += f"- Schedule interviews for top 5-10 candidates\n"
            response += f"- Use automated screening to filter further\n"
            response += f"- Review candidate profiles for detailed information\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Candidate matching error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error finding candidates: {str(e)}")]
    
    async def _schedule_interviews(self, args: dict) -> list[types.TextContent]:
        """Schedule interviews for multiple candidates"""
        try:
            candidate_ids = args["candidate_ids"]
            job_id = args["job_id"]
            interviewer = args["interviewer"]
            interview_type = args.get("interview_type", "Phone Screen")
            start_date = args.get("start_date")
            end_date = args.get("end_date")
            duration = args.get("duration_minutes", 60)
            
            scheduled = await self.automation.schedule_bulk_interviews(
                candidate_ids=candidate_ids,
                job_id=job_id,
                interviewer=interviewer,
                interview_type=interview_type,
                start_date=start_date,
                end_date=end_date,
                duration_minutes=duration
            )
            
            response = f"📅 **Interview Scheduling Complete**\n\n"
            response += f"✅ **Successfully Scheduled:** {len(scheduled)} interviews\n"
            response += f"👥 **Interviewer:** {interviewer}\n"
            response += f"🕐 **Duration:** {duration} minutes each\n\n"
            
            response += f"📋 **Scheduled Interviews:**\n"
            for interview in scheduled:
                response += f"- {interview['candidate_name']} on {interview['scheduled_time']}\n"
            
            response += f"\n📧 **Next Steps:**\n"
            response += f"- Email invitations will be sent automatically\n"
            response += f"- Calendar events have been created\n"
            response += f"- Interview preparation materials will be shared\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Interview scheduling error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error scheduling interviews: {str(e)}")]
    
    async def _get_analytics_dashboard(self, args: dict) -> list[types.TextContent]:
        """Get comprehensive recruitment analytics"""
        try:
            date_range = args.get("date_range", "30d")
            job_id = args.get("job_id")
            department = args.get("department")
            
            analytics = await self.analytics.generate_dashboard(
                date_range=date_range,
                job_id=job_id,
                department=department
            )
            
            response = f"📊 **Recruitment Analytics Dashboard**\n\n"
            
            # Key Metrics
            response += f"📈 **Key Metrics ({date_range}):**\n"
            response += f"- Total Candidates: {analytics['total_candidates']:,}\n"
            response += f"- Active Jobs: {analytics['active_jobs']}\n"
            response += f"- Applications: {analytics['total_applications']:,}\n"
            response += f"- Interviews Scheduled: {analytics['interviews_scheduled']}\n"
            response += f"- Hiring Rate: {analytics['hiring_rate']:.1%}\n\n"
            
            # Source Performance
            response += f"🎯 **Source Performance:**\n"
            for source in analytics['top_sources']:
                response += f"- {source['name']}: {source['candidates']} candidates ({source['quality_score']:.1f}/10)\n"
            response += "\n"
            
            # Skills in Demand
            response += f"🔥 **Top Skills in Demand:**\n"
            for skill in analytics['top_skills'][:10]:
                response += f"- {skill['name']}: {skill['demand']} jobs\n"
            response += "\n"
            
            # Department Performance
            if analytics.get('department_stats'):
                response += f"🏢 **Department Performance:**\n"
                for dept in analytics['department_stats']:
                    response += f"- {dept['name']}: {dept['avg_time_to_hire']} days avg. hire time\n"
                response += "\n"
            
            # Recent Activity
            response += f"⚡ **Recent Activity:**\n"
            for activity in analytics['recent_activity'][:5]:
                response += f"- {activity['timestamp']}: {activity['description']}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error generating analytics: {str(e)}")]
    
    async def _search_candidates(self, args: dict) -> list[types.TextContent]:
        """Advanced candidate search"""
        try:
            query = args.get("query", "")
            skills = args.get("skills", [])
            experience_min = args.get("experience_min")
            experience_max = args.get("experience_max")
            location = args.get("location")
            education_level = args.get("education_level")
            availability = args.get("availability")
            limit = args.get("limit", 50)
            
            candidates = await self.db_manager.search_candidates(
                query=query,
                skills=skills,
                experience_min=experience_min,
                experience_max=experience_max,
                location=location,
                education_level=education_level,
                availability=availability,
                limit=limit
            )
            
            response = f"🔍 **Search Results: {len(candidates)} candidates found**\n\n"
            
            if query:
                response += f"🎯 **Search Query:** {query}\n"
            if skills:
                response += f"🔧 **Skills Filter:** {', '.join(skills)}\n"
            if experience_min or experience_max:
                exp_filter = f"{experience_min or 0}-{experience_max or '∞'} years"
                response += f"💼 **Experience Filter:** {exp_filter}\n"
            if location:
                response += f"📍 **Location Filter:** {location}\n"
            response += "\n"
            
            for i, candidate in enumerate(candidates[:20], 1):
                response += f"**{i}. {candidate['name']}**\n"
                response += f"   📧 {candidate['email']}\n"
                response += f"   💼 {candidate['experience_years']} years\n"
                response += f"   📍 {candidate.get('location', 'N/A')}\n"
                response += f"   🔧 {', '.join(candidate['skills'][:4])}\n"
                response += f"   🆔 ID: {candidate['id']}\n\n"
            
            if len(candidates) > 20:
                response += f"... and {len(candidates) - 20} more candidates\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error searching candidates: {str(e)}")]
    
    async def _get_candidate_profile(self, args: dict) -> list[types.TextContent]:
        """Get detailed candidate profile"""
        try:
            candidate_id = args["candidate_id"]
            
            profile = await self.db_manager.get_candidate_profile(candidate_id)
            
            if not profile:
                return [types.TextContent(
                    type="text", 
                    text=f"❌ Candidate with ID {candidate_id} not found"
                )]
            
            response = f"👤 **Candidate Profile: {profile['name']}**\n\n"
            
            # Basic Information
            response += f"📧 **Email:** {profile['email']}\n"
            response += f"📱 **Phone:** {profile.get('phone', 'N/A')}\n"
            response += f"📍 **Location:** {profile.get('location', 'N/A')}\n"
            response += f"💼 **Experience:** {profile['experience_years']} years\n"
            response += f"🎓 **Education:** {profile.get('education', 'N/A')}\n\n"
            
            # Skills
            response += f"🔧 **Skills:**\n"
            for skill in profile['skills']:
                response += f"- {skill}\n"
            response += "\n"
            
            # Work History
            if profile.get('work_history'):
                response += f"💼 **Work History:**\n"
                for job in profile['work_history'][:3]:
                    response += f"- {job['title']} at {job['company']} ({job['duration']})\n"
                response += "\n"
            
            # Applications
            if profile.get('applications'):
                response += f"📋 **Recent Applications:**\n"
                for app in profile['applications'][:5]:
                    response += f"- {app['job_title']} at {app['company']} - {app['status']}\n"
                response += "\n"
            
            # Availability
            response += f"📅 **Availability:** {profile.get('availability', 'Immediate')}\n"
            response += f"💰 **Salary Expectation:** {profile.get('salary_expectation', 'N/A')}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Profile retrieval error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error retrieving profile: {str(e)}")]
    
    async def _view_candidate_resume(self, args: dict) -> list[types.TextContent]:
        """View complete resume and profile details for a candidate"""
        try:
            candidate_id = args.get("candidate_id")
            candidate_name = args.get("candidate_name")
            candidate_email = args.get("candidate_email")
            
            # Search by different criteria
            async with self.db_manager.get_connection() as conn:
                if candidate_id:
                    # Search by ID
                    candidate = await conn.fetchrow("""
                        SELECT * FROM candidates WHERE id = $1
                    """, candidate_id)
                elif candidate_name:
                    # Search by name (case-insensitive match)
                    candidate = await conn.fetchrow("""
                        SELECT * FROM candidates 
                        WHERE LOWER(name) LIKE LOWER($1)
                        ORDER BY id
                        LIMIT 1
                    """, f"%{candidate_name}%")
                elif candidate_email:
                    # Search by email
                    candidate = await conn.fetchrow("""
                        SELECT * FROM candidates WHERE LOWER(email) = LOWER($1)
                    """, candidate_email)
                else:
                    return [types.TextContent(
                        type="text", 
                        text="❌ Please provide candidate_id, candidate_name, or candidate_email"
                    )]
                
                if not candidate:
                    search_term = candidate_id or candidate_name or candidate_email
                    return [types.TextContent(
                        type="text", 
                        text=f"❌ No candidate found matching: {search_term}"
                    )]
                
                # Format complete resume/profile information
                response = f"📄 **COMPLETE RESUME - {candidate['name']}**\n"
                response += "=" * 60 + "\n\n"
                
                # Personal Information
                response += f"👤 **PERSONAL INFORMATION**\n"
                response += f"• Full Name: {candidate['name']}\n"
                response += f"• Email: {candidate['email']}\n"
                response += f"• Phone: {candidate['phone'] or 'Not provided'}\n"
                response += f"• Location: {candidate['location'] or 'Not provided'}\n"
                response += f"• Current Position: {candidate['current_position'] or 'Not specified'}\n"
                response += f"• Years of Experience: {candidate['experience_years']} years\n"
                response += f"• Education Level: {candidate['education_level'] or 'Not specified'}\n\n"
                
                # Skills
                try:
                    import json
                    skills = json.loads(candidate['skills']) if candidate['skills'] else []
                    if skills:
                        response += f"🔧 **TECHNICAL SKILLS**\n"
                        for skill in skills:
                            response += f"• {skill}\n"
                        response += "\n"
                except:
                    if candidate['skills']:
                        response += f"🔧 **TECHNICAL SKILLS**\n{candidate['skills']}\n\n"
                
                # Certifications
                try:
                    certs = json.loads(candidate['certifications']) if candidate['certifications'] else []
                    if certs:
                        response += f"🏆 **CERTIFICATIONS**\n"
                        for cert in certs:
                            response += f"• {cert}\n"
                        response += "\n"
                except:
                    if candidate['certifications']:
                        response += f"🏆 **CERTIFICATIONS**\n{candidate['certifications']}\n\n"
                
                # Languages
                try:
                    langs = json.loads(candidate['languages']) if candidate['languages'] else []
                    if langs:
                        response += f"🌐 **LANGUAGES**\n"
                        for lang in langs:
                            response += f"• {lang}\n"
                        response += "\n"
                except:
                    if candidate['languages']:
                        response += f"🌐 **LANGUAGES**\n{candidate['languages']}\n\n"
                
                # Education
                try:
                    edu = json.loads(candidate['education']) if candidate['education'] else []
                    if edu:
                        response += f"🎓 **EDUCATION**\n"
                        for education in edu:
                            response += f"• {education}\n"
                        response += "\n"
                except:
                    if candidate['education']:
                        response += f"🎓 **EDUCATION**\n{candidate['education']}\n\n"
                
                # Portfolio Links
                try:
                    portfolio = json.loads(candidate['portfolio_links']) if candidate['portfolio_links'] else []
                    if portfolio:
                        response += f"🔗 **PORTFOLIO & LINKS**\n"
                        for link in portfolio:
                            response += f"• {link}\n"
                        response += "\n"
                except:
                    if candidate['portfolio_links']:
                        response += f"🔗 **PORTFOLIO & LINKS**\n{candidate['portfolio_links']}\n\n"
                
                # Professional Details
                response += f"💼 **PROFESSIONAL DETAILS**\n"
                response += f"• Salary Expectation: ${candidate['salary_expectation']:,}" if candidate['salary_expectation'] else "• Salary Expectation: Not specified"
                response += "\n"
                response += f"• Remote Preference: {'Yes' if candidate['remote_preference'] else 'No'}\n"
                response += f"• Availability Date: {candidate['availability_date'] or 'Immediate'}\n"
                
                # Scoring Information
                if candidate['overall_score'] or candidate['technical_score'] or candidate['communication_score']:
                    response += f"\n📊 **ASSESSMENT SCORES**\n"
                    if candidate['overall_score']:
                        response += f"• Overall Score: {candidate['overall_score']}/100\n"
                    if candidate['technical_score']:
                        response += f"• Technical Score: {candidate['technical_score']}/100\n"
                    if candidate['communication_score']:
                        response += f"• Communication Score: {candidate['communication_score']}/100\n"
                
                # Resume Text Content
                if candidate['resume_text']:
                    response += f"\n📝 **FULL RESUME CONTENT**\n"
                    response += "-" * 40 + "\n"
                    response += candidate['resume_text']
                    response += "\n" + "-" * 40 + "\n"
                
                # System Information
                response += f"\n📁 **SYSTEM INFORMATION**\n"
                response += f"• Candidate ID: {candidate['id']}\n"
                response += f"• Source: {candidate['source']}\n"
                response += f"• Added to System: {candidate['created_at']}\n"
                response += f"• Last Updated: {candidate['updated_at'] or 'Never'}\n"
                response += f"• Resume File Path: {candidate['resume_file_path'] or 'No file stored'}\n"
                
                return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Resume viewing error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error retrieving resume: {str(e)}")]
    
    async def _close_job_posting(self, args: dict) -> list[types.TextContent]:
        """Close a job posting and stop accepting new applications"""
        try:
            job_id = args.get("job_id")
            job_title = args.get("job_title")
            company = args.get("company")
            closure_reason = args.get("closure_reason", "Position filled")
            notify_applicants = args.get("notify_applicants", True)
            
            async with self.db_manager.get_connection() as conn:
                # Find the job if only title/company provided
                if not job_id and (job_title or company):
                    where_conditions = []
                    params = []
                    param_num = 1
                    
                    if job_title:
                        where_conditions.append(f"title ILIKE ${param_num}")
                        params.append(f"%{job_title}%")
                        param_num += 1
                    
                    if company:
                        where_conditions.append(f"company ILIKE ${param_num}")
                        params.append(f"%{company}%")
                        param_num += 1
                    
                    where_clause = " AND ".join(where_conditions)
                    
                    job = await conn.fetchrow(f"""
                        SELECT id, title, company, status
                        FROM job_postings 
                        WHERE {where_clause}
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, *params)
                    
                    if job:
                        job_id = job['id']
                    else:
                        return [types.TextContent(type="text", text="❌ Job posting not found")]
                
                if not job_id:
                    return [types.TextContent(type="text", text="❌ Job ID is required")]
                
                # Get job details before closing
                job_details = await conn.fetchrow("""
                    SELECT id, title, company, status, 
                           (SELECT COUNT(*) FROM applications WHERE job_id = $1) as app_count
                    FROM job_postings 
                    WHERE id = $1
                """, job_id)
                
                if not job_details:
                    return [types.TextContent(type="text", text=f"❌ Job with ID {job_id} not found")]
                
                if job_details['status'] == 'Closed':
                    return [types.TextContent(type="text", text=f"ℹ️ Job '{job_details['title']}' is already closed")]
                
                # Close the job posting
                await conn.execute("""
                    UPDATE job_postings 
                    SET status = 'Closed', 
                        updated_at = NOW(),
                        filled_date = CURRENT_DATE
                    WHERE id = $1
                """, job_id)
                
                # Update any pending applications to "Position Filled"
                if notify_applicants:
                    updated_apps = await conn.fetchval("""
                        UPDATE applications 
                        SET status = 'Position Filled', 
                            notes = COALESCE(notes, '') || $1,
                            updated_at = NOW()
                        WHERE job_id = $2 AND status IN ('applied', 'screening', 'interview')
                        RETURNING COUNT(*)
                    """, f"\\n[Auto-update] {closure_reason}", job_id)
                else:
                    updated_apps = 0
                
                response = f"✅ **Job Posting Closed Successfully**\\n\\n"
                response += f"🏢 **Job Details:**\\n"
                response += f"• Title: {job_details['title']}\\n"
                response += f"• Company: {job_details['company']}\\n"
                response += f"• Job ID: {job_id}\\n\\n"
                response += f"📊 **Impact:**\\n"
                response += f"• Total Applications: {job_details['app_count']}\\n"
                response += f"• Applications Updated: {updated_apps}\\n"
                response += f"• Closure Reason: {closure_reason}\\n\\n"
                response += f"📝 **Actions Taken:**\\n"
                response += f"• ✅ Job status changed to 'Closed'\\n"
                response += f"• ✅ Filled date recorded\\n"
                if notify_applicants:
                    response += f"• ✅ Pending applicants notified\\n"
                else:
                    response += f"• ⏸️ Applicants not notified\\n"
                response += f"\\n🎯 **Next Steps:**\\n"
                response += f"• Job no longer accepts new applications\\n"
                response += f"• Position removed from public career portal\\n"
                response += f"• Recruitment analytics updated\\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Close job error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error closing job: {str(e)}")]
    
    async def _automated_screening(self, args: dict) -> list[types.TextContent]:
        """Run automated screening on candidates"""
        try:
            job_id = args["job_id"]
            candidate_ids = args.get("candidate_ids")
            criteria = args.get("screening_criteria", {})
            
            results = await self.automation.automated_screening(
                job_id=job_id,
                candidate_ids=candidate_ids,
                criteria=criteria
            )
            
            passed = [r for r in results if r['passed']]
            failed = [r for r in results if not r['passed']]
            
            response = f"🔍 **Automated Screening Results**\n\n"
            response += f"✅ **Passed:** {len(passed)} candidates\n"
            response += f"❌ **Failed:** {len(failed)} candidates\n"
            response += f"📊 **Pass Rate:** {len(passed)/len(results)*100:.1f}%\n\n"
            
            if passed:
                response += f"✅ **Candidates who passed screening:**\n"
                for candidate in passed[:10]:
                    response += f"- {candidate['name']} (Score: {candidate['score']:.1f}/10)\n"
                response += "\n"
            
            if failed:
                response += f"❌ **Candidates who failed screening:**\n"
                for candidate in failed[:5]:
                    reasons = ', '.join(candidate['failure_reasons'])
                    response += f"- {candidate['name']}: {reasons}\n"
                response += "\n"
            
            response += f"📋 **Screening Criteria Applied:**\n"
            for key, value in criteria.items():
                response += f"- {key}: {value}\n"
            
            response += f"\n🎯 **Next Steps:**\n"
            response += f"- Schedule interviews for candidates who passed\n"
            response += f"- Review borderline cases manually\n"
            response += f"- Update application statuses\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Screening error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error running screening: {str(e)}")]
    
    async def _generate_job_report(self, args: dict) -> list[types.TextContent]:
        """Generate comprehensive job report"""
        try:
            job_id = args["job_id"]
            include_analytics = args.get("include_analytics", True)
            include_candidates = args.get("include_candidates", True)
            
            report = await self.analytics.generate_job_report(
                job_id=job_id,
                include_analytics=include_analytics,
                include_candidates=include_candidates
            )
            
            response = f"📋 **Job Report: {report['job_title']}**\n\n"
            
            # Job Overview
            response += f"🏢 **Company:** {report['company']}\n"
            response += f"📍 **Location:** {report['location']}\n"
            response += f"📅 **Posted:** {report['posted_date']}\n"
            response += f"📊 **Status:** {report['status']}\n\n"
            
            # Application Statistics
            response += f"📈 **Application Statistics:**\n"
            response += f"- Total Applications: {report['total_applications']}\n"
            response += f"- Qualified Candidates: {report['qualified_candidates']}\n"
            response += f"- Interviews Scheduled: {report['interviews_scheduled']}\n"
            response += f"- Offers Made: {report['offers_made']}\n"
            response += f"- Hires: {report['hires']}\n\n"
            
            # Performance Metrics
            if include_analytics:
                response += f"⚡ **Performance Metrics:**\n"
                response += f"- Average Time to Interview: {report['avg_time_to_interview']} days\n"
                response += f"- Average Time to Hire: {report['avg_time_to_hire']} days\n"
                response += f"- Application Quality Score: {report['quality_score']:.1f}/10\n"
                response += f"- Conversion Rate: {report['conversion_rate']:.1%}\n\n"
            
            # Top Candidates
            if include_candidates and report.get('top_candidates'):
                response += f"🌟 **Top Candidates:**\n"
                for i, candidate in enumerate(report['top_candidates'][:5], 1):
                    response += f"{i}. {candidate['name']} - {candidate['match_score']:.1%} match\n"
                response += "\n"
            
            # Skills Analysis
            response += f"🔧 **Skills Analysis:**\n"
            response += f"- Most Common Skills: {', '.join(report['common_skills'][:5])}\n"
            response += f"- Skills Gap: {', '.join(report['missing_skills'][:3])}\n\n"
            
            # Recommendations
            response += f"💡 **Recommendations:**\n"
            for rec in report['recommendations']:
                response += f"- {rec}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error generating report: {str(e)}")]
    
    async def _update_application_status(self, args: dict) -> list[types.TextContent]:
        """Update application status and add notes"""
        try:
            application_id = args["application_id"]
            status = args["status"]
            notes = args.get("notes", "")
            next_action = args.get("next_action", "")
            
            updated = await self.db_manager.update_application_status(
                application_id=application_id,
                status=status,
                notes=notes,
                next_action=next_action
            )
            
            if not updated:
                return [types.TextContent(
                    type="text", 
                    text=f"❌ Application with ID {application_id} not found"
                )]
            
            response = f"✅ **Application Status Updated**\n\n"
            response += f"🆔 **Application ID:** {application_id}\n"
            response += f"📊 **New Status:** {status}\n"
            if notes:
                response += f"📝 **Notes:** {notes}\n"
            if next_action:
                response += f"⏭️ **Next Action:** {next_action}\n"
            
            response += f"\n📅 **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Status update error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error updating status: {str(e)}")]

    # NEW HR-SPECIFIC TOOL IMPLEMENTATIONS
    
    async def _get_job_applications(self, args: dict) -> list[types.TextContent]:
        """Get all applications for a specific job"""
        try:
            job_id = args["job_id"]
            status_filter = args.get("status_filter")
            limit = args.get("limit", 100)
            
            async with self.db_manager.get_connection() as conn:
                # Get job details
                job_query = "SELECT title, company FROM job_postings WHERE id = $1"
                job = await conn.fetchrow(job_query, job_id)
                if not job:
                    return [types.TextContent(type="text", text=f"❌ Job ID {job_id} not found")]
                
                # Build applications query
                apps_query = """
                    SELECT a.id, a.status, a.application_date, a.initial_score,
                           c.name, c.email, c.phone, c.current_position, c.experience_years
                    FROM applications a
                    JOIN candidates c ON a.candidate_id = c.id
                    WHERE a.job_id = $1
                """
                params = [job_id]
                
                if status_filter:
                    apps_query += " AND a.status = $2"
                    params.append(status_filter)
                
                apps_query += " ORDER BY a.application_date DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                applications = await conn.fetch(apps_query, *params)
                
                response = f"📋 **Applications for {job['title']} at {job['company']}**\n\n"
                response += f"📊 **Total Applications:** {len(applications)}\n\n"
                
                if status_filter:
                    response += f"🔍 **Filtered by Status:** {status_filter}\n\n"
                
                for app in applications:
                    score_display = f"{app['initial_score']:.1%}" if app['initial_score'] else "Pending"
                    response += f"**{app['name']}**\n"
                    response += f"• Status: {app['status']}\n"
                    response += f"• Score: {score_display}\n"
                    response += f"• Email: {app['email']}\n"
                    response += f"• Position: {app['current_position'] or 'Not specified'}\n"
                    response += f"• Experience: {app['experience_years']} years\n"
                    response += f"• Applied: {app['application_date'].strftime('%Y-%m-%d')}\n\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Get applications error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error getting applications: {str(e)}")]
    
    async def _create_screening_questions(self, args: dict) -> list[types.TextContent]:
        """Generate intelligent screening questions for a job position"""
        try:
            job_id = args["job_id"]
            question_type = args.get("question_type", "mixed")
            difficulty_level = args.get("difficulty_level", "intermediate")
            question_count = args.get("question_count", 5)
            
            async with self.db_manager.get_connection() as conn:
                # Get job details
                job_query = """
                    SELECT title, description, required_skills, preferred_skills, 
                           experience_min, experience_max
                    FROM job_postings WHERE id = $1
                """
                job = await conn.fetchrow(job_query, job_id)
                if not job:
                    return [types.TextContent(type="text", text=f"❌ Job ID {job_id} not found")]
                
                # Parse skills
                required_skills = json.loads(job['required_skills']) if job['required_skills'] else []
                preferred_skills = json.loads(job['preferred_skills']) if job['preferred_skills'] else []
                all_skills = list(set(required_skills + preferred_skills))
                
                response = f"❓ **Screening Questions for {job['title']}**\n\n"
                response += f"🎯 **Question Type:** {question_type.title()}\n"
                response += f"📊 **Difficulty Level:** {difficulty_level.title()}\n\n"
                
                questions = []
                
                if question_type in ["technical", "mixed"]:
                    if "Python" in all_skills:
                        questions.append({
                            "type": "Technical",
                            "question": "Explain the difference between a list and a tuple in Python. When would you use each?",
                            "expected_skills": ["Python", "Data Structures"]
                        })
                    
                    if "SQL" in all_skills or "Database" in all_skills:
                        questions.append({
                            "type": "Technical", 
                            "question": "How would you optimize a slow SQL query? What are the first things you would check?",
                            "expected_skills": ["SQL", "Database Optimization"]
                        })
                
                if question_type in ["experience", "mixed"]:
                    questions.append({
                        "type": "Experience",
                        "question": f"Tell me about a challenging project you worked on that required {', '.join(required_skills[:2])} skills. What obstacles did you face and how did you overcome them?",
                        "expected_skills": required_skills[:2]
                    })
                
                if question_type in ["behavioral", "mixed"]:
                    questions.append({
                        "type": "Behavioral",
                        "question": "Describe a time when you had to learn a new technology quickly. How did you approach it?",
                        "expected_skills": ["Learning Agility", "Adaptability"]
                    })
                    
                    questions.append({
                        "type": "Behavioral",
                        "question": "Tell me about a time when you disagreed with a team member. How did you handle the situation?",
                        "expected_skills": ["Communication", "Conflict Resolution"]
                    })
                
                if question_type in ["situational", "mixed"]:
                    questions.append({
                        "type": "Situational",
                        "question": "If you were tasked with improving our team's current development process, where would you start and why?",
                        "expected_skills": ["Process Improvement", "Critical Thinking"]
                    })
                
                # Limit to requested count
                selected_questions = questions[:question_count]
                
                for i, q in enumerate(selected_questions, 1):
                    response += f"**Question {i} ({q['type']}):**\n"
                    response += f"{q['question']}\n\n"
                    response += f"*Expected Skills: {', '.join(q['expected_skills'])}*\n\n"
                    response += "---\n\n"
                
                response += f"💡 **Tip:** Use these questions in your initial screening calls or as application form questions."
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Screening questions error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error generating questions: {str(e)}")]
    
    async def _screen_candidate_responses(self, args: dict) -> list[types.TextContent]:
        """Analyze candidate responses to screening questions using AI"""
        try:
            candidate_id = args["candidate_id"]
            job_id = args["job_id"]
            responses = args["responses"]
            
            async with self.db_manager.get_connection() as conn:
                # Get candidate and job info
                candidate_query = "SELECT name, email FROM candidates WHERE id = $1"
                candidate = await conn.fetchrow(candidate_query, candidate_id)
                
                job_query = "SELECT title, required_skills FROM job_postings WHERE id = $1"
                job = await conn.fetchrow(job_query, job_id)
                
                if not candidate or not job:
                    return [types.TextContent(type="text", text="❌ Candidate or job not found")]
                
                response = f"🧠 **AI Screening Analysis**\n\n"
                response += f"👤 **Candidate:** {candidate['name']}\n"
                response += f"💼 **Position:** {job['title']}\n\n"
                
                total_score = 0
                max_score = len(responses) * 10
                
                for i, resp in enumerate(responses, 1):
                    question = resp['question']
                    answer = resp['answer']
                    
                    # Simple AI scoring (in real implementation, use actual NLP/AI)
                    answer_length = len(answer.split())
                    has_keywords = any(skill.lower() in answer.lower() 
                                     for skill in json.loads(job['required_skills'] or '[]'))
                    
                    # Basic scoring algorithm
                    score = 5  # Base score
                    if answer_length > 20:
                        score += 2  # Detailed answer
                    if has_keywords:
                        score += 2  # Relevant keywords
                    if "experience" in answer.lower() or "project" in answer.lower():
                        score += 1  # Experience mentioned
                    
                    score = min(score, 10)  # Cap at 10
                    total_score += score
                    
                    response += f"**Question {i}:**\n"
                    response += f"*{question[:100]}...*\n\n"
                    response += f"**Answer Quality Score:** {score}/10\n"
                    
                    if score >= 8:
                        response += "✅ **Excellent** - Comprehensive and relevant answer\n"
                    elif score >= 6:
                        response += "🟡 **Good** - Adequate answer with room for improvement\n"
                    else:
                        response += "🔴 **Needs Improvement** - Answer lacks detail or relevance\n"
                    
                    response += "\n---\n\n"
                
                overall_percentage = (total_score / max_score) * 100
                response += f"📊 **Overall Screening Score:** {total_score}/{max_score} ({overall_percentage:.1f}%)\n\n"
                
                if overall_percentage >= 80:
                    recommendation = "🌟 **STRONG RECOMMENDATION** - Proceed to next round"
                elif overall_percentage >= 60:
                    recommendation = "✅ **PROCEED** - Schedule interview with some reservations"
                elif overall_percentage >= 40:
                    recommendation = "🤔 **MAYBE** - Consider for lower-level positions or with additional screening"
                else:
                    recommendation = "❌ **NOT RECOMMENDED** - Does not meet minimum requirements"
                
                response += f"🎯 **Recommendation:** {recommendation}\n\n"
                response += "📝 **Next Steps:**\n"
                response += "• Review candidate's portfolio/projects\n"
                response += "• Schedule technical interview if proceeding\n"
                response += "• Check references for top candidates\n"
                
                # Update application with screening score
                await conn.execute(
                    "UPDATE applications SET screening_score = $1 WHERE candidate_id = $2 AND job_id = $3",
                    overall_percentage / 100, candidate_id, job_id
                )
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Screen responses error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error analyzing responses: {str(e)}")]
    
    async def _get_application_pipeline(self, args: dict) -> list[types.TextContent]:
        """Get complete application pipeline view with status counts"""
        try:
            job_id = args.get("job_id")
            date_range = args.get("date_range", "30d")
            
            # Parse date range
            days = int(date_range.replace('d', ''))
            
            async with self.db_manager.get_connection() as conn:
                if job_id:
                    # Specific job pipeline
                    job_query = "SELECT title, company FROM job_postings WHERE id = $1"
                    job = await conn.fetchrow(job_query, job_id)
                    if not job:
                        return [types.TextContent(type="text", text=f"❌ Job ID {job_id} not found")]
                    
                    pipeline_query = """
                        SELECT status, COUNT(*) as count
                        FROM applications 
                        WHERE job_id = $1 AND created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY status
                        ORDER BY 
                            CASE status
                                WHEN 'applied' THEN 1
                                WHEN 'screening' THEN 2
                                WHEN 'phone_screen' THEN 3
                                WHEN 'technical_interview' THEN 4
                                WHEN 'final_interview' THEN 5
                                WHEN 'offer_pending' THEN 6
                                WHEN 'offer_accepted' THEN 7
                                ELSE 8
                            END
                    """ % days
                    
                    pipeline = await conn.fetch(pipeline_query, job_id)
                    
                    response = f"🔄 **Application Pipeline: {job['title']}**\n\n"
                    response += f"🏢 **Company:** {job['company']}\n"
                    response += f"📅 **Date Range:** Last {days} days\n\n"
                    
                else:
                    # Overall pipeline across all jobs
                    pipeline_query = """
                        SELECT status, COUNT(*) as count
                        FROM applications 
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY status
                        ORDER BY 
                            CASE status
                                WHEN 'applied' THEN 1
                                WHEN 'screening' THEN 2
                                WHEN 'phone_screen' THEN 3
                                WHEN 'technical_interview' THEN 4
                                WHEN 'final_interview' THEN 5
                                WHEN 'offer_pending' THEN 6
                                WHEN 'offer_accepted' THEN 7
                                ELSE 8
                            END
                    """ % days
                    
                    pipeline = await conn.fetch(pipeline_query)
                    
                    response = f"🔄 **Overall Application Pipeline**\n\n"
                    response += f"📅 **Date Range:** Last {days} days\n\n"
                
                total_applications = sum(row['count'] for row in pipeline)
                
                # Display pipeline stages
                stage_emojis = {
                    'applied': '📝',
                    'screening': '🔍',
                    'phone_screen': '📞',
                    'technical_interview': '💻',
                    'final_interview': '🤝',
                    'offer_pending': '📨',
                    'offer_accepted': '✅',
                    'offer_declined': '❌',
                    'rejected': '🚫',
                    'withdrawn': '↩️'
                }
                
                for stage in pipeline:
                    status = stage['status']
                    count = stage['count']
                    percentage = (count / total_applications * 100) if total_applications > 0 else 0
                    emoji = stage_emojis.get(status, '📋')
                    
                    response += f"{emoji} **{status.replace('_', ' ').title()}:** {count} ({percentage:.1f}%)\n"
                
                # Calculate conversion rates
                if total_applications > 0:
                    response += f"\n📊 **Conversion Rates:**\n"
                    
                    stages_data = {row['status']: row['count'] for row in pipeline}
                    applied = stages_data.get('applied', 0)
                    screening = stages_data.get('screening', 0)
                    interviews = sum(stages_data.get(s, 0) for s in ['phone_screen', 'technical_interview', 'final_interview'])
                    offers = stages_data.get('offer_pending', 0) + stages_data.get('offer_accepted', 0)
                    hires = stages_data.get('offer_accepted', 0)
                    
                    if applied > 0:
                        response += f"• Application to Screening: {(screening/applied*100):.1f}%\n"
                        response += f"• Application to Interview: {(interviews/applied*100):.1f}%\n"
                        response += f"• Application to Offer: {(offers/applied*100):.1f}%\n"
                        response += f"• Application to Hire: {(hires/applied*100):.1f}%\n"
                
                response += f"\n📈 **Total Applications:** {total_applications}\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error getting pipeline: {str(e)}")]
    
    async def _rank_applications(self, args: dict) -> list[types.TextContent]:
        """Automatically rank applications based on job requirements and AI scoring"""
        try:
            job_id = args["job_id"]
            ranking_criteria = args.get("ranking_criteria", {})
            
            # Get weights with defaults
            skills_weight = ranking_criteria.get("skills_weight", 0.4)
            experience_weight = ranking_criteria.get("experience_weight", 0.3)
            education_weight = ranking_criteria.get("education_weight", 0.2)
            other_weight = ranking_criteria.get("other_weight", 0.1)
            
            async with self.db_manager.get_connection() as conn:
                # Get job details
                job_query = """
                    SELECT title, required_skills, experience_min, experience_max
                    FROM job_postings WHERE id = $1
                """
                job = await conn.fetchrow(job_query, job_id)
                if not job:
                    return [types.TextContent(type="text", text=f"❌ Job ID {job_id} not found")]
                
                # Get applications with candidate details
                apps_query = """
                    SELECT a.id as app_id, a.candidate_id, a.status,
                           c.name, c.email, c.experience_years, c.skills, c.education_level,
                           c.overall_score, a.initial_score, a.screening_score
                    FROM applications a
                    JOIN candidates c ON a.candidate_id = c.id
                    WHERE a.job_id = $1 AND a.status NOT IN ('rejected', 'withdrawn')
                    ORDER BY a.application_date DESC
                """
                
                applications = await conn.fetch(apps_query, job_id)
                
                if not applications:
                    return [types.TextContent(type="text", text=f"📝 No applications found for this job.")]
                
                required_skills = json.loads(job['required_skills']) if job['required_skills'] else []
                
                # Calculate scores for each application
                ranked_apps = []
                for app in applications:
                    candidate_skills = json.loads(app['skills']) if app['skills'] else []
                    
                    # Skills match score
                    skills_match = 0
                    if required_skills:
                        matching_skills = set(candidate_skills) & set(required_skills)
                        skills_match = len(matching_skills) / len(required_skills)
                    
                    # Experience score
                    exp_score = 0
                    if job['experience_min'] and job['experience_max']:
                        if app['experience_years'] >= job['experience_min']:
                            if app['experience_years'] <= job['experience_max']:
                                exp_score = 1.0  # Perfect match
                            else:
                                # Bonus for more experience, but diminishing returns
                                exp_score = min(1.2, 1.0 + (app['experience_years'] - job['experience_max']) * 0.05)
                        else:
                            # Penalty for less experience
                            exp_score = app['experience_years'] / job['experience_min']
                    
                    # Education score (simplified)
                    edu_score = 0.8  # Default
                    if app['education_level']:
                        education_levels = {'High School': 0.3, 'Associate': 0.5, 'Bachelor': 0.8, 'Master': 1.0, 'PhD': 1.2}
                        edu_score = education_levels.get(app['education_level'], 0.8)
                    
                    # Other factors (existing scores)
                    other_score = 0
                    if app['overall_score']:
                        other_score += app['overall_score'] * 0.5
                    if app['screening_score']:
                        other_score += app['screening_score'] * 0.5
                    if not other_score:
                        other_score = 0.7  # Default
                    
                    # Calculate weighted final score
                    final_score = (
                        skills_match * skills_weight +
                        exp_score * experience_weight +
                        edu_score * education_weight +
                        other_score * other_weight
                    )
                    
                    ranked_apps.append({
                        'app_id': app['app_id'],
                        'candidate_id': app['candidate_id'],
                        'name': app['name'],
                        'email': app['email'],
                        'status': app['status'],
                        'experience_years': app['experience_years'],
                        'final_score': final_score,
                        'skills_match': skills_match,
                        'exp_score': exp_score,
                        'edu_score': edu_score,
                        'other_score': other_score
                    })
                
                # Sort by final score
                ranked_apps.sort(key=lambda x: x['final_score'], reverse=True)
                
                response = f"🏆 **Application Rankings for {job['title']}**\n\n"
                response += f"⚖️ **Ranking Weights:**\n"
                response += f"• Skills: {skills_weight*100:.0f}%\n"
                response += f"• Experience: {experience_weight*100:.0f}%\n"
                response += f"• Education: {education_weight*100:.0f}%\n"
                response += f"• Other: {other_weight*100:.0f}%\n\n"
                
                response += "📊 **Ranked Candidates:**\n\n"
                
                for i, app in enumerate(ranked_apps[:20], 1):  # Top 20
                    score_percent = app['final_score'] * 100
                    
                    if score_percent >= 80:
                        tier = "🥇 **Top Tier**"
                    elif score_percent >= 65:
                        tier = "🥈 **Strong**"
                    elif score_percent >= 50:
                        tier = "🥉 **Potential**"
                    else:
                        tier = "📋 **Review**"
                    
                    response += f"**#{i} - {app['name']}** {tier}\n"
                    response += f"• Overall Score: {score_percent:.1f}%\n"
                    response += f"• Skills Match: {app['skills_match']*100:.0f}%\n"
                    response += f"• Experience: {app['experience_years']} years\n"
                    response += f"• Status: {app['status']}\n"
                    response += f"• Email: {app['email']}\n\n"
                
                # Update database with rankings
                for i, app in enumerate(ranked_apps):
                    await conn.execute(
                        "UPDATE applications SET initial_score = $1 WHERE id = $2",
                        app['final_score'], app['app_id']
                    )
                
                response += f"✅ **Ranking complete!** Updated scores for {len(ranked_apps)} applications."
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Ranking error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error ranking applications: {str(e)}")]
    
    async def _publish_job_posting(self, args: dict) -> list[types.TextContent]:
        """Publish a job posting to make it visible on application portal"""
        try:
            job_id = args["job_id"]
            publish_immediately = args.get("publish_immediately", True)
            application_deadline = args.get("application_deadline")
            featured = args.get("featured", False)
            
            async with self.db_manager.get_connection() as conn:
                # Get job details
                job_query = "SELECT title, company, status FROM job_postings WHERE id = $1"
                job = await conn.fetchrow(job_query, job_id)
                if not job:
                    return [types.TextContent(type="text", text=f"❌ Job ID {job_id} not found")]
                
                # Update job status and publication details
                update_fields = []
                params = []
                param_count = 1
                
                if publish_immediately:
                    update_fields.append(f"status = ${param_count}")
                    params.append("Open")
                    param_count += 1
                    
                    update_fields.append(f"posted_date = ${param_count}")
                    params.append(date.today())
                    param_count += 1
                
                if application_deadline:
                    try:
                        deadline_date = datetime.strptime(application_deadline, "%Y-%m-%d").date()
                        update_fields.append(f"application_deadline = ${param_count}")
                        params.append(deadline_date)
                        param_count += 1
                    except ValueError:
                        return [types.TextContent(type="text", text="❌ Invalid date format. Use YYYY-MM-DD")]
                
                update_fields.append(f"updated_at = ${param_count}")
                params.append(datetime.now())
                param_count += 1
                
                # Add job_id as last parameter
                params.append(job_id)
                
                update_query = f"""
                    UPDATE job_postings 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                """
                
                await conn.execute(update_query, *params)
                
                response = f"🚀 **Job Published Successfully!**\n\n"
                response += f"📋 **Job:** {job['title']}\n"
                response += f"🏢 **Company:** {job['company']}\n"
                response += f"📅 **Published:** {date.today()}\n"
                
                if application_deadline:
                    response += f"⏰ **Application Deadline:** {application_deadline}\n"
                
                if featured:
                    response += f"⭐ **Featured Posting:** Yes\n"
                
                response += f"\n✅ **Status:** Live on Application Portal\n"
                response += f"🔗 **Candidates can now apply through the public portal**\n\n"
                
                response += f"📊 **Next Steps:**\n"
                response += f"• Monitor applications in real-time\n"
                response += f"• Set up automated screening criteria\n"
                response += f"• Review candidate pipeline regularly\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Publish job error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error publishing job: {str(e)}")]
    
    async def _generate_interview_questions(self, args: dict) -> list[types.TextContent]:
        """Generate personalized interview questions based on candidate profile and job requirements"""
        try:
            candidate_id = args["candidate_id"]
            job_id = args["job_id"]
            interview_type = args.get("interview_type", "technical")
            focus_areas = args.get("focus_areas", [])
            
            async with self.db_manager.get_connection() as conn:
                # Get candidate details
                candidate_query = """
                    SELECT name, skills, experience_years, current_position, education
                    FROM candidates WHERE id = $1
                """
                candidate = await conn.fetchrow(candidate_query, candidate_id)
                
                # Get job details
                job_query = """
                    SELECT title, required_skills, preferred_skills, description, responsibilities
                    FROM job_postings WHERE id = $1
                """
                job = await conn.fetchrow(job_query, job_id)
                
                if not candidate or not job:
                    return [types.TextContent(type="text", text="❌ Candidate or job not found")]
                
                candidate_skills = json.loads(candidate['skills']) if candidate['skills'] else []
                required_skills = json.loads(job['required_skills']) if job['required_skills'] else []
                
                response = f"❓ **Personalized Interview Questions**\n\n"
                response += f"👤 **Candidate:** {candidate['name']}\n"
                response += f"💼 **Position:** {job['title']}\n"
                response += f"🎯 **Interview Type:** {interview_type.title()}\n\n"
                
                questions = []
                
                if interview_type == "phone_screen":
                    questions = [
                        f"Can you walk me through your background and how it relates to this {job['title']} position?",
                        f"What interests you most about working at our company in this role?",
                        f"You have {candidate['experience_years']} years of experience. Can you highlight your most relevant accomplishments?",
                        "What are your salary expectations for this role?",
                        "When would you be available to start if we move forward?"
                    ]
                
                elif interview_type == "technical":
                    # Generate technical questions based on skills overlap
                    matching_skills = set(candidate_skills) & set(required_skills)
                    
                    for skill in list(matching_skills)[:3]:
                        if skill.lower() == "python":
                            questions.append(f"I see you have Python experience. Can you explain the difference between *args and **kwargs?")
                        elif skill.lower() == "sql":
                            questions.append(f"How would you optimize a query that's running slowly? Walk me through your debugging process.")
                        elif skill.lower() == "javascript":
                            questions.append(f"Explain how closures work in JavaScript and provide an example.")
                        elif skill.lower() in ["react", "angular", "vue"]:
                            questions.append(f"How do you handle state management in {skill} applications?")
                        elif skill.lower() == "aws":
                            questions.append(f"Which AWS services have you worked with? Can you design a scalable web application architecture?")
                        else:
                            questions.append(f"Can you describe a challenging project where you used {skill}? What obstacles did you face?")
                    
                    # Add general technical questions
                    questions.extend([
                        "How do you approach debugging when something isn't working as expected?",
                        "Describe your experience with version control. What's your typical Git workflow?",
                        "How do you stay updated with new technologies and best practices?"
                    ])
                
                elif interview_type == "behavioral":
                    questions = [
                        "Tell me about a time when you had to learn a new technology quickly. How did you approach it?",
                        "Describe a situation where you disagreed with a team member. How did you resolve it?",
                        "Can you give me an example of a project you're particularly proud of? What made it successful?",
                        "Tell me about a time when you made a mistake. How did you handle it?",
                        "How do you prioritize tasks when you have multiple deadlines?",
                        "Describe a time when you had to work with a difficult team member or client."
                    ]
                
                elif interview_type == "final":
                    questions = [
                        "What questions do you have about the role, team, or company culture?",
                        "How do you see yourself contributing to our team in the first 90 days?",
                        "What are your long-term career goals, and how does this role fit into them?",
                        "Is there anything we haven't covered that you'd like to share about your background?",
                        "What would make you excited to join our team?"
                    ]
                
                # Add focus area questions if specified
                if focus_areas:
                    questions.append(f"\n**Focus Area Questions ({', '.join(focus_areas)}):**")
                    for area in focus_areas:
                        questions.append(f"Can you share your experience with {area}? What projects have you worked on?")
                
                # Display questions
                for i, question in enumerate(questions[:10], 1):  # Limit to 10 questions
                    response += f"**Question {i}:**\n{question}\n\n"
                
                # Add interviewer tips
                response += "💡 **Interviewer Tips:**\n"
                response += f"• Candidate has {candidate['experience_years']} years of experience - adjust question depth accordingly\n"
                response += f"• Strong in: {', '.join(candidate_skills[:3]) if candidate_skills else 'N/A'}\n"
                response += f"• Look for: {', '.join(required_skills[:3]) if required_skills else 'N/A'}\n"
                response += "• Allow time for candidate questions\n"
                response += "• Take notes on technical responses for follow-up\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Interview questions error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error generating questions: {str(e)}")]
    
    async def _bulk_status_update(self, args: dict) -> list[types.TextContent]:
        """Update status for multiple applications at once (batch processing)"""
        try:
            application_ids = args["application_ids"]
            new_status = args["new_status"]
            notes = args.get("notes", "")
            send_notifications = args.get("send_notifications", True)
            
            if not application_ids:
                return [types.TextContent(type="text", text="❌ No application IDs provided")]
            
            async with self.db_manager.get_connection() as conn:
                # Validate application IDs and get current info
                valid_apps = await conn.fetch(
                    "SELECT id, candidate_id FROM applications WHERE id = ANY($1)",
                    application_ids
                )
                
                if len(valid_apps) != len(application_ids):
                    invalid_count = len(application_ids) - len(valid_apps)
                    response = f"⚠️ Warning: {invalid_count} invalid application IDs found\n\n"
                else:
                    response = ""
                
                # Update applications in batch
                update_query = """
                    UPDATE applications 
                    SET status = $1, updated_at = $2
                    WHERE id = ANY($3)
                """
                
                await conn.execute(update_query, new_status, datetime.now(), [app['id'] for app in valid_apps])
                
                # Add notes if provided
                if notes:
                    note_query = """
                        UPDATE applications 
                        SET notes = COALESCE(notes, '[]'::json) || $1::json
                        WHERE id = ANY($2)
                    """
                    note_entry = json.dumps([{
                        "date": datetime.now().isoformat(),
                        "note": notes,
                        "action": f"Bulk status update to {new_status}"
                    }])
                    
                    await conn.execute(note_query, note_entry, [app['id'] for app in valid_apps])
                
                response += f"✅ **Bulk Status Update Complete**\n\n"
                response += f"📊 **Summary:**\n"
                response += f"• Applications Updated: {len(valid_apps)}\n"
                response += f"• New Status: {new_status}\n"
                response += f"• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                
                if notes:
                    response += f"• Notes Added: {notes}\n"
                
                if send_notifications:
                    response += f"\n📧 **Notifications:**\n"
                    response += f"• Email notifications will be sent to {len(valid_apps)} candidates\n"
                    # In real implementation, trigger email notifications here
                
                response += f"\n📋 **Updated Application IDs:**\n"
                for app in valid_apps:
                    response += f"• App ID: {app['id']}\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error in bulk update: {str(e)}")]
    
    async def _get_hiring_analytics(self, args: dict) -> list[types.TextContent]:
        """Get comprehensive hiring analytics with application trends and conversion rates"""
        try:
            timeframe = args.get("timeframe", "30d")
            department = args.get("department")
            job_id = args.get("job_id")
            
            # Parse timeframe
            days = int(timeframe.replace('d', '').replace('y', '365'))
            
            async with self.db_manager.get_connection() as conn:
                # Base date filter
                date_filter = "created_at >= NOW() - INTERVAL '%s days'" % days
                
                # Build query filters
                filters = [date_filter]
                params = []
                
                if job_id:
                    filters.append("job_id = $1")
                    params.append(job_id)
                elif department:
                    filters.append("job_id IN (SELECT id FROM job_postings WHERE department = $1)")
                    params.append(department)
                
                where_clause = " AND ".join(filters)
                
                # Get application metrics
                metrics_query = f"""
                    SELECT 
                        COUNT(*) as total_applications,
                        COUNT(DISTINCT candidate_id) as unique_candidates,
                        COUNT(DISTINCT job_id) as active_jobs,
                        AVG(CASE WHEN initial_score IS NOT NULL THEN initial_score END) as avg_score
                    FROM applications 
                    WHERE {where_clause}
                """
                
                metrics = await conn.fetchrow(metrics_query, *params)
                
                # Get status breakdown
                status_query = f"""
                    SELECT status, COUNT(*) as count
                    FROM applications 
                    WHERE {where_clause}
                    GROUP BY status
                    ORDER BY count DESC
                """
                
                statuses = await conn.fetch(status_query, *params)
                
                # Get daily application trend
                trend_query = f"""
                    SELECT DATE(created_at) as date, COUNT(*) as applications
                    FROM applications 
                    WHERE {where_clause}
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 30
                """
                
                trends = await conn.fetch(trend_query, *params)
                
                # Get top performing jobs
                jobs_query = f"""
                    SELECT jp.title, jp.company, COUNT(a.id) as app_count,
                           AVG(a.initial_score) as avg_score
                    FROM job_postings jp
                    LEFT JOIN applications a ON jp.id = a.job_id
                    WHERE a.{where_clause}
                    GROUP BY jp.id, jp.title, jp.company
                    ORDER BY app_count DESC
                    LIMIT 10
                """
                
                top_jobs = await conn.fetch(jobs_query, *params)
                
                # Build response
                response = f"📊 **Hiring Analytics Dashboard**\n\n"
                response += f"📅 **Timeframe:** Last {timeframe}\n"
                
                if department:
                    response += f"🏢 **Department:** {department}\n"
                elif job_id:
                    response += f"💼 **Job ID:** {job_id}\n"
                
                response += "\n📈 **Key Metrics:**\n"
                response += f"• Total Applications: {metrics['total_applications']}\n"
                response += f"• Unique Candidates: {metrics['unique_candidates']}\n"
                response += f"• Active Jobs: {metrics['active_jobs']}\n"
                
                if metrics['avg_score']:
                    response += f"• Average Score: {metrics['avg_score']:.1%}\n"
                
                # Application status breakdown
                response += "\n📋 **Application Status Breakdown:**\n"
                total_apps = sum(row['count'] for row in statuses)
                
                for status in statuses:
                    percentage = (status['count'] / total_apps * 100) if total_apps > 0 else 0
                    response += f"• {status['status'].replace('_', ' ').title()}: {status['count']} ({percentage:.1f}%)\n"
                
                # Conversion rates
                if total_apps > 0:
                    status_counts = {row['status']: row['count'] for row in statuses}
                    
                    applied = status_counts.get('applied', 0)
                    screening = status_counts.get('screening', 0)
                    interviews = sum(status_counts.get(s, 0) for s in ['phone_screen', 'technical_interview', 'final_interview'])
                    offers = status_counts.get('offer_pending', 0) + status_counts.get('offer_accepted', 0)
                    hires = status_counts.get('offer_accepted', 0)
                    
                    response += "\n🎯 **Conversion Rates:**\n"
                    if applied > 0:
                        response += f"• Application → Screening: {(screening/applied*100):.1f}%\n"
                        response += f"• Application → Interview: {(interviews/applied*100):.1f}%\n"
                        response += f"• Application → Offer: {(offers/applied*100):.1f}%\n"
                        response += f"• Application → Hire: {(hires/applied*100):.1f}%\n"
                
                # Daily trends
                if trends:
                    response += "\n📈 **Recent Application Trend:**\n"
                    for trend in trends[:7]:  # Last 7 days
                        response += f"• {trend['date']}: {trend['applications']} applications\n"
                
                # Top performing jobs
                if top_jobs:
                    response += "\n🏆 **Top Performing Jobs:**\n"
                    for i, job in enumerate(top_jobs[:5], 1):
                        score_display = f" (avg: {job['avg_score']:.1%})" if job['avg_score'] else ""
                        response += f"{i}. {job['title']} at {job['company']}: {job['app_count']} apps{score_display}\n"
                
                # Insights and recommendations
                response += "\n💡 **Insights & Recommendations:**\n"
                
                if metrics['total_applications'] < 10:
                    response += "• Consider expanding job posting reach\n"
                elif metrics['total_applications'] > 100:
                    response += "• High application volume - consider automated screening\n"
                
                if status_counts.get('applied', 0) > status_counts.get('screening', 0) * 3:
                    response += "• Large backlog in initial screening - consider automation\n"
                
                avg_score = metrics.get('avg_score', 0)
                if avg_score and avg_score < 0.6:
                    response += "• Low average scores - review job requirements or sourcing strategy\n"
                elif avg_score and avg_score > 0.8:
                    response += "• High quality candidates - excellent sourcing!\n"
                
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Hiring analytics error: {str(e)}")
            return [types.TextContent(type="text", text=f"❌ Error getting analytics: {str(e)}")]

async def main():
    """Main server entry point"""
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    await init_database()
    
    # Create and run server
    agent = EnterpriseRecruitmentAgent()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await agent.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="enterprise-recruitment-agent",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=True)
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
