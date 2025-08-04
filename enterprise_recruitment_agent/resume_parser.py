"""
Advanced Resume Parser for Enterprise Recruitment Agent

Handles bulk resume processing with AI-powered extraction of structured data.
Supports PDF, DOCX, and TXT formats with intelligent skill and experience extraction.
"""

import asyncio
import base64
import io
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import PyPDF2
import docx
from dataclasses import asdict

from models import CandidateProfile

logger = logging.getLogger(__name__)


class ResumeParser:
    """Advanced resume parser with AI-powered extraction"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)  # For parallel processing
        
        # Skill categories for better matching
        self.skill_categories = {
            'programming_languages': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 
                'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB'
            ],
            'web_technologies': [
                'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 
                'Flask', 'Spring', 'Laravel', 'HTML', 'CSS', 'Bootstrap', 'Tailwind'
            ],
            'databases': [
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle',
                'SQL Server', 'Cassandra', 'DynamoDB', 'Elasticsearch'
            ],
            'cloud_platforms': [
                'AWS', 'Azure', 'Google Cloud', 'GCP', 'DigitalOcean', 'Heroku',
                'Vercel', 'Netlify', 'Docker', 'Kubernetes', 'Terraform'
            ],
            'data_science': [
                'Machine Learning', 'Deep Learning', 'Data Science', 'Pandas',
                'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Tableau', 'Power BI'
            ],
            'mobile_development': [
                'iOS', 'Android', 'React Native', 'Flutter', 'Xamarin', 'Ionic'
            ],
            'devops': [
                'CI/CD', 'Jenkins', 'GitLab CI', 'GitHub Actions', 'Docker',
                'Kubernetes', 'Ansible', 'Terraform', 'Monitoring', 'Logging'
            ],
            'project_management': [
                'Agile', 'Scrum', 'Kanban', 'JIRA', 'Confluence', 'Trello',
                'Asana', 'Project Management', 'Team Leadership'
            ]
        }
        
        # All skills for pattern matching
        self.all_skills = []
        for category_skills in self.skill_categories.values():
            self.all_skills.extend(category_skills)
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in\s*(?:the\s*)?(?:field|industry)',
        ]
        
        # Education patterns
        self.education_patterns = {
            'PhD': [r'ph\.?d\.?', r'doctorate', r'doctoral'],
            'Masters': [r'master\'?s?', r'm\.s\.?', r'm\.a\.?', r'mba', r'm\.sc\.?'],
            'Bachelors': [r'bachelor\'?s?', r'b\.s\.?', r'b\.a\.?', r'b\.sc\.?', r'b\.tech'],
            'Associates': [r'associate\'?s?', r'a\.a\.?', r'a\.s\.?'],
            'High School': [r'high\s*school', r'diploma', r'ged']
        }
        
        # Contact information patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    
    async def parse_resume_bulk(self, resume_data: List[Tuple[str, str]]) -> List[CandidateProfile]:
        """Parse multiple resumes in parallel"""
        tasks = []
        for file_content, filename in resume_data:
            task = asyncio.create_task(self._parse_single_resume(file_content, filename))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error parsing resume {resume_data[i][1]}: {result}")
                continue
            candidates.append(result)
        
        return candidates
    
    async def _parse_single_resume(self, file_content: str, filename: str) -> CandidateProfile:
        """Parse a single resume file"""
        # Decode base64 content
        try:
            file_bytes = base64.b64decode(file_content)
        except Exception as e:
            logger.error(f"Error decoding file {filename}: {e}")
            return self._create_empty_candidate(filename)
        
        # Extract text based on file type
        text = await self._extract_text(file_bytes, filename)
        
        if not text or len(text.strip()) < 50:
            logger.warning(f"Insufficient text extracted from {filename}")
            return self._create_empty_candidate(filename)
        
        # Parse structured data from text
        return await self._parse_candidate_data(text, filename)
    
    async def _extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from file based on extension"""
        file_extension = filename.lower().split('.')[-1]
        
        try:
            if file_extension == 'pdf':
                return await self._extract_from_pdf(file_bytes)
            elif file_extension in ['docx', 'doc']:
                return await self._extract_from_docx(file_bytes)
            elif file_extension == 'txt':
                return file_bytes.decode('utf-8', errors='ignore')
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""
    
    async def _extract_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        def extract():
            try:
                pdf_file = io.BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                return ""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, extract)
    
    async def _extract_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        def extract():
            try:
                docx_file = io.BytesIO(file_bytes)
                doc = docx.Document(docx_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except Exception as e:
                logger.error(f"DOCX extraction error: {e}")
                return ""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, extract)
    
    async def _parse_candidate_data(self, text: str, filename: str) -> CandidateProfile:
        """Parse structured candidate data from resume text"""
        text_lower = text.lower()
        
        # Extract basic information
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        
        # Extract professional information
        skills = self._extract_skills(text)
        experience_years = self._extract_experience_years(text)
        current_position = self._extract_current_position(text)
        
        # Extract education
        education_level = self._extract_education_level(text)
        education_details = self._extract_education_details(text)
        
        # Extract other information
        certifications = self._extract_certifications(text)
        languages = self._extract_languages(text)
        location = self._extract_location(text)
        
        # Calculate scores
        overall_score = self._calculate_overall_score(skills, experience_years, education_level)
        technical_score = self._calculate_technical_score(skills)
        
        return CandidateProfile(
            name=name or f"Candidate_{filename}",
            email=email or "",
            phone=phone,
            location=location,
            current_position=current_position,
            experience_years=experience_years,
            skills=skills,
            certifications=certifications,
            languages=languages,
            education=education_details,
            education_level=education_level,
            resume_text=text,
            source="Resume Upload",
            overall_score=overall_score,
            technical_score=technical_score,
            created_at=datetime.now()
        )
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume"""
        lines = text.strip().split('\n')
        
        # Usually the name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            
            # Skip lines that are clearly not names
            if not line or len(line) < 3 or len(line) > 50:
                continue
                
            if any(keyword in line.lower() for keyword in ['resume', 'cv', 'email', '@', 'phone', 'address']):
                continue
            
            # Check if it looks like a name (2-4 words, mostly letters)
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.replace('.', '').replace(',', '').isalpha() for word in words):
                return line
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume"""
        matches = re.findall(self.email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume"""
        matches = re.findall(self.phone_pattern, text)
        return matches[0] if matches else None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_upper = text.upper()
        found_skills = []
        
        # Direct skill matching
        for skill in self.all_skills:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.upper()) + r'\b'
            if re.search(pattern, text_upper):
                found_skills.append(skill)
        
        # Look for skills in dedicated sections
        skills_section = self._extract_section(text, ['skills', 'technical skills', 'technologies'])
        if skills_section:
            # Extract additional skills from skills section
            additional_skills = self._extract_skills_from_section(skills_section)
            found_skills.extend(additional_skills)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        
        return unique_skills[:20]  # Limit to top 20 skills
    
    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        """Extract additional skills from a dedicated skills section"""
        additional_skills = []
        
        # Common programming patterns
        programming_patterns = [
            r'\b(React|Angular|Vue)\b',
            r'\b(Node\.js|Express\.js)\b',
            r'\b(REST|GraphQL|API)\b',
            r'\b(Git|GitHub|GitLab)\b',
            r'\b(Linux|Unix|Windows)\b',
        ]
        
        for pattern in programming_patterns:
            matches = re.findall(pattern, section_text, re.IGNORECASE)
            additional_skills.extend(matches)
        
        return additional_skills
    
    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience from resume"""
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = int(matches[0])
                    return min(years, 50)  # Cap at 50 years
                except ValueError:
                    continue
        
        # Alternative: count job positions and estimate
        experience_section = self._extract_section(text, ['experience', 'work history', 'employment'])
        if experience_section:
            # Count years mentioned in date ranges
            year_pattern = r'(19|20)\d{2}'
            years = re.findall(year_pattern, experience_section)
            if len(years) >= 2:
                try:
                    years_int = [int(year) for year in years]
                    return min(max(years_int) - min(years_int), 50)
                except ValueError:
                    pass
        
        return 0
    
    def _extract_current_position(self, text: str) -> Optional[str]:
        """Extract current job position"""
        experience_section = self._extract_section(text, ['experience', 'work history', 'employment'])
        
        if experience_section:
            lines = experience_section.split('\n')[:10]  # Look at first 10 lines
            
            for line in lines:
                line = line.strip()
                
                # Look for common job title patterns
                job_patterns = [
                    r'(senior|sr\.?|lead|principal|chief)\s+(\w+\s*){1,3}(engineer|developer|manager|architect|analyst)',
                    r'(software|web|mobile|full[\s-]?stack)\s+(engineer|developer)',
                    r'(project|product|engineering|technical)\s+manager',
                    r'(data|business|systems)\s+analyst',
                    r'(ui/ux|ux|ui)\s+designer'
                ]
                
                for pattern in job_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group().title()
        
        return None
    
    def _extract_education_level(self, text: str) -> Optional[str]:
        """Extract highest education level"""
        text_lower = text.lower()
        
        for level, patterns in self.education_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return level
        
        return None
    
    def _extract_education_details(self, text: str) -> List[Dict[str, Any]]:
        """Extract detailed education information"""
        education_section = self._extract_section(text, ['education', 'academic', 'qualifications'])
        
        if not education_section:
            return []
        
        # This is a simplified version - could be enhanced with more sophisticated parsing
        return [{
            'degree': self._extract_education_level(education_section),
            'field': 'Computer Science',  # Default - could be enhanced
            'institution': 'University',  # Could be extracted
            'year': None  # Could be extracted
        }]
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from resume"""
        cert_patterns = [
            r'\b(AWS|Azure|Google Cloud|GCP)\s+(Certified|Certification)\b',
            r'\bPMP\b',
            r'\bCSM\b',
            r'\bCISSP\b',
            r'\bCEH\b',
            r'\bCPA\b',
            r'\bFRM\b',
            r'\bCFA\b',
        ]
        
        certifications = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)
        
        return certifications
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract programming and spoken languages"""
        # Programming languages are already in skills
        # This could extract spoken languages
        language_patterns = [
            r'\b(English|Spanish|French|German|Chinese|Japanese|Korean|Hindi|Arabic)\b'
        ]
        
        languages = []
        for pattern in language_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            languages.extend(matches)
        
        return list(set(languages))
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from resume"""
        location_patterns = [
            r'([A-Z][a-z]+,\s*[A-Z]{2})',  # City, State
            r'([A-Z][a-z]+\s*[A-Z][a-z]*,\s*[A-Z]{2})',  # City Name, State
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_section(self, text: str, section_keywords: List[str]) -> Optional[str]:
        """Extract a specific section from resume"""
        lines = text.split('\n')
        
        start_idx = None
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            if any(keyword in line_lower for keyword in section_keywords):
                start_idx = i
                break
        
        if start_idx is None:
            return None
        
        # Find the end of the section (next section or end of text)
        end_idx = len(lines)
        section_keywords_all = [
            'experience', 'education', 'skills', 'projects', 'certifications',
            'achievements', 'awards', 'references', 'summary', 'objective'
        ]
        
        for i in range(start_idx + 1, len(lines)):
            line_lower = lines[i].lower().strip()
            
            # Check if this line starts a new section
            if (line_lower and 
                any(keyword in line_lower for keyword in section_keywords_all) and
                not any(keyword in line_lower for keyword in section_keywords)):
                end_idx = i
                break
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def _calculate_overall_score(self, skills: List[str], experience_years: int, education_level: Optional[str]) -> float:
        """Calculate overall candidate score"""
        score = 0.0
        
        # Skills contribution (40%)
        skills_score = min(len(skills) / 10.0, 1.0) * 40
        score += skills_score
        
        # Experience contribution (40%)
        experience_score = min(experience_years / 10.0, 1.0) * 40
        score += experience_score
        
        # Education contribution (20%)
        education_scores = {
            'PhD': 20,
            'Masters': 16,
            'Bachelors': 12,
            'Associates': 8,
            'High School': 4
        }
        education_score = education_scores.get(education_level, 0)
        score += education_score
        
        return round(score, 2)
    
    def _calculate_technical_score(self, skills: List[str]) -> float:
        """Calculate technical skills score"""
        technical_skills = 0
        
        for skill in skills:
            if skill in self.skill_categories['programming_languages']:
                technical_skills += 2
            elif skill in self.skill_categories['web_technologies']:
                technical_skills += 1.5
            elif skill in self.skill_categories['databases']:
                technical_skills += 1.5
            elif skill in self.skill_categories['cloud_platforms']:
                technical_skills += 2
            elif skill in self.skill_categories['data_science']:
                technical_skills += 2
            else:
                technical_skills += 1
        
        return round(min(technical_skills, 100.0), 2)
    
    def _create_empty_candidate(self, filename: str) -> CandidateProfile:
        """Create an empty candidate profile for failed parsing"""
        return CandidateProfile(
            name=f"Failed_Parse_{filename}",
            email="",
            source="Resume Upload - Failed",
            created_at=datetime.now()
        )
