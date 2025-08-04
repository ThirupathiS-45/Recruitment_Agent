"""
Email Service Module for Enterprise Recruitment Agent

Handles all email communications including:
- Interview confirmations and invitations
- Application status updates
- Automated notifications
- Calendar invites
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Professional email service for recruitment communications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email_address = os.getenv('EMAIL_ADDRESS', 'hr@company.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.company_name = os.getenv('COMPANY_NAME', 'TechCorp')
        
    async def send_interview_confirmation(self, candidate_email: str, candidate_name: str, 
                                        interview_details: Dict) -> bool:
        """Send interview confirmation email to candidate"""
        try:
            subject = f"Interview Scheduled - {interview_details['job_title']} Position"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎉 Interview Scheduled!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                            We're excited to meet with you
                        </p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p style="font-size: 16px; margin-bottom: 25px;">
                            Dear <strong>{candidate_name}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 25px;">
                            Great news! We've scheduled your interview for the 
                            <strong>{interview_details['job_title']}</strong> position at {self.company_name}.
                        </p>
                        
                        <div style="background: white; padding: 25px; border-radius: 8px; 
                                    border-left: 4px solid #667eea; margin: 25px 0;">
                            <h3 style="color: #667eea; margin-top: 0;">📅 Interview Details</h3>
                            
                            <div style="display: grid; gap: 15px;">
                                <div><strong>📍 Position:</strong> {interview_details['job_title']}</div>
                                <div><strong>👤 Interviewer:</strong> {interview_details['interviewer']}</div>
                                <div><strong>📅 Date:</strong> {interview_details['date']}</div>
                                <div><strong>🕐 Time:</strong> {interview_details['time']}</div>
                                <div><strong>⏰ Duration:</strong> {interview_details['duration']} minutes</div>
                                <div><strong>💻 Type:</strong> {interview_details['type']}</div>
                                {f"<div><strong>🔗 Meeting Link:</strong> <a href='{interview_details.get('meeting_link', '')}'>{interview_details.get('meeting_link', 'Will be shared separately')}</a></div>" if interview_details['type'] == 'Remote' else ""}
                            </div>
                        </div>
                        
                        <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h4 style="color: #0066cc; margin-top: 0;">📋 What to Expect</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>The interview will focus on your technical skills and experience</li>
                                <li>Please prepare examples of your past work and achievements</li>
                                <li>Feel free to ask questions about the role and our company</li>
                                <li>We'll discuss next steps and timeline at the end</li>
                            </ul>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h4 style="color: #856404; margin-top: 0;">💼 Preparation Tips</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Review the job description and requirements</li>
                                <li>Prepare your portfolio or work samples</li>
                                <li>Research our company and recent projects</li>
                                <li>Test your camera and microphone (for remote interviews)</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 16px; margin: 25px 0;">
                            If you need to reschedule or have any questions, please don't hesitate to contact us 
                            at <a href="mailto:{self.email_address}">{self.email_address}</a> or reply to this email.
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 25px; 
                                    border-top: 2px solid #eee;">
                            <p style="font-size: 16px; margin-bottom: 15px;">
                                Looking forward to meeting you! 🌟
                            </p>
                            <p style="font-size: 14px; color: #666; margin: 0;">
                                Best regards,<br>
                                <strong>HR Team</strong><br>
                                {self.company_name}
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Check if email is properly configured
            if (self.email_address == "your-hr-email@company.com" or 
                self.email_password == "your-app-password" or 
                not self.email_password):
                # Demo mode - log the email instead of sending
                logger.info(f"📧 DEMO MODE: Interview confirmation email would be sent to: {candidate_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Interview scheduled for {candidate_name} with {interview_details['interviewer']}")
                print(f"📧 DEMO: Email confirmation logged for {candidate_name} ({candidate_email})")
                return True
            else:
                # Real email sending
                success = await self._send_email(candidate_email, subject, html_body)
                if success:
                    logger.info(f"✅ Real email sent to {candidate_email}")
                    print(f"✅ Interview confirmation email sent to {candidate_name}")
                else:
                    logger.error(f"❌ Failed to send real email to {candidate_email}")
                    print(f"❌ Failed to send email to {candidate_name}")
                return success
            
        except Exception as e:
            logger.error(f"Failed to send interview confirmation: {str(e)}")
            return False
    
    async def send_application_received(self, candidate_email: str, candidate_name: str, 
                                      job_title: str) -> bool:
        """Send application received confirmation"""
        try:
            subject = f"Application Received - {job_title} Position"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                                color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">✅ Application Received!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                            Thank you for your interest in joining our team
                        </p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p style="font-size: 16px; margin-bottom: 25px;">
                            Dear <strong>{candidate_name}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 25px;">
                            Thank you for applying for the <strong>{job_title}</strong> position at {self.company_name}. 
                            We have successfully received your application and our HR team will review it shortly.
                        </p>
                        
                        <div style="background: white; padding: 25px; border-radius: 8px; 
                                    border-left: 4px solid #28a745; margin: 25px 0;">
                            <h3 style="color: #28a745; margin-top: 0;">📋 What's Next?</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Our HR team will review your application within 5-7 business days</li>
                                <li>If you're a good fit, we'll contact you to schedule an interview</li>
                                <li>You'll receive updates on your application status via email</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 16px; margin: 25px 0;">
                            If you have any questions about your application or the position, 
                            please feel free to contact us at <a href="mailto:{self.email_address}">{self.email_address}</a>.
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 25px; 
                                    border-top: 2px solid #eee;">
                            <p style="font-size: 14px; color: #666; margin: 0;">
                                Best regards,<br>
                                <strong>HR Team</strong><br>
                                {self.company_name}
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # For demo purposes, log the email
            logger.info(f"📧 Application received email would be sent to: {candidate_email}")
            logger.info(f"Subject: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send application confirmation: {str(e)}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Actually send email via SMTP (for real implementation)"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_address
            message["To"] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
