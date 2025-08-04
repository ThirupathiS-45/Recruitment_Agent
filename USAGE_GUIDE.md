# Enterprise Recruitment Agent - Usage Guide

This comprehensive guide explains how to use the Enterprise Recruitment Agent through two different interfaces: Streamlit Web UI and Claude Desktop integration.

## Table of Contents
1. [System Overview](#system-overview)
2. [Streamlit Web UI](#streamlit-web-ui)
3. [Claude Desktop Integration](#claude-desktop-integration)
4. [Database Setup](#database-setup)
5. [Features and Capabilities](#features-and-capabilities)

## System Overview

The Enterprise Recruitment Agent is designed to handle large-scale recruitment operations (1000+ resumes) with advanced AI-powered features:

- **Bulk Resume Processing**: Process thousands of resumes efficiently
- **AI-Powered Matching**: Advanced candidate-job matching algorithms
- **Automated Screening**: Rule-based and AI-driven screening
- **Analytics Dashboard**: Comprehensive recruitment insights
- **Workflow Automation**: End-to-end process automation

## Streamlit Web UI

### Starting the Web Interface

1. **Open Terminal/Command Prompt** in the project directory:
   ```bash
   cd c:\Users\thiru\OneDrive\Desktop\recruitment_agent
   ```

2. **Run the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Access the web interface**:
   - Local URL: http://localhost:8501
   - Network URL: http://10.3.19.49:8501

### Web Interface Features

#### 1. Dashboard Tab
- **Real-time Metrics**: Active candidates, open positions, recent matches
- **Interactive Charts**: 
  - Applications over time
  - Top skills in demand
  - Success rate by position type
- **Quick Actions**: Upload resumes, create job posts, run analytics

#### 2. Candidates Tab
- **Search & Filter**: Find candidates by name, skills, experience
- **Candidate Profiles**: View detailed candidate information
- **Bulk Operations**: Process multiple candidates simultaneously
- **Export Options**: Download candidate data in various formats

#### 3. Jobs Tab
- **Job Management**: Create, edit, and manage job postings
- **Requirements Tracking**: Monitor skill requirements and priorities
- **Application Status**: Track application progress
- **Matching Candidates**: View best-fit candidates for each position

#### 4. Bulk Upload Tab
- **File Upload**: Support for PDF, DOCX, and TXT resume formats
- **Batch Processing**: Upload and process multiple files at once
- **Progress Tracking**: Real-time processing status
- **Results Summary**: View processing results and extracted data

#### 5. AI Matching Tab
- **Intelligent Matching**: AI-powered candidate-job matching
- **Scoring Algorithms**: View match scores and reasoning
- **Filtering Options**: Filter by match score, skills, experience
- **Recommendations**: Get AI suggestions for best matches

#### 6. Analytics Tab
- **Performance Metrics**: Recruitment KPIs and success rates
- **Trend Analysis**: Historical data and trends
- **Skill Analytics**: Most in-demand skills and gaps
- **Interactive Visualizations**: Charts and graphs for insights

#### 7. Settings Tab
- **Database Configuration**: Manage database connections
- **Processing Settings**: Configure bulk processing parameters
- **AI Model Settings**: Adjust matching algorithms
- **Export Preferences**: Set default export formats

## Claude Desktop Integration

### Setup Instructions

1. **Install Claude Desktop** (if not already installed):
   - Download from https://claude.ai/download
   - Install and set up your account

2. **Configure MCP Server**:
   - Copy the `claude_desktop_config.json` file to your Claude Desktop configuration directory
   - Typical locations:
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
     - Linux: `~/.config/Claude/claude_desktop_config.json`

3. **Restart Claude Desktop** for the configuration to take effect

### Using MCP Tools in Claude Desktop

Once configured, you can use natural language commands in Claude Desktop:

#### Bulk Resume Processing
```
"Process 500 resumes from the uploads folder and extract skills, experience, and contact information"
```

#### Candidate Search
```
"Find all candidates with Python and machine learning experience, minimum 3 years"
```

#### Job Matching
```
"Find the top 10 candidates for the Senior Software Engineer position"
```

#### Analytics
```
"Generate a recruitment analytics report for the last quarter"
```

#### Automated Screening
```
"Screen all new candidates for the marketing positions using our standard criteria"
```

## Database Setup

### PostgreSQL Configuration

1. **Ensure PostgreSQL is running** with the following credentials:
   - Host: localhost
   - Port: 5432
   - Database: recruitment_db
   - Username: postgres
   - Password: techy@123

2. **Database will be automatically created** when you first run the system

3. **Tables and schema** are created automatically with proper indexing for performance

### Environment Variables

The system uses the following environment variables (automatically configured):
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=techy@123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=recruitment_db
```

## Features and Capabilities

### 1. Resume Parsing
- **Multiple Formats**: PDF, DOCX, TXT support
- **AI-Powered Extraction**: Skills, experience, education, certifications
- **Bulk Processing**: Handle 1000+ resumes efficiently
- **Error Handling**: Robust processing with detailed error reporting

### 2. Candidate Matching
- **Semantic Similarity**: Advanced NLP-based matching
- **Skill Mapping**: Intelligent skill relationship understanding
- **Experience Weighting**: Factor in experience levels and relevance
- **Custom Scoring**: Configurable matching algorithms

### 3. Workflow Automation
- **Automated Screening**: Rule-based candidate filtering
- **Interview Scheduling**: Calendar integration and automation
- **Email Templates**: Automated communication workflows
- **Status Tracking**: End-to-end process monitoring

### 4. Analytics and Reporting
- **Real-time Dashboards**: Live recruitment metrics
- **Trend Analysis**: Historical performance tracking
- **Success Metrics**: Conversion rates and KPIs
- **Custom Reports**: Flexible reporting options

### 5. Scalability Features
- **Async Processing**: Non-blocking operations for large datasets
- **Connection Pooling**: Optimized database performance
- **Batch Operations**: Efficient bulk data handling
- **Caching**: Smart caching for frequently accessed data

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Verify PostgreSQL is running
   - Check credentials in environment variables
   - Ensure database exists

2. **Streamlit Import Error**:
   - Run: `pip install streamlit plotly pandas`
   - Verify all dependencies are installed

3. **MCP Server Not Found**:
   - Check Claude Desktop configuration file
   - Verify file paths are correct
   - Restart Claude Desktop

4. **Performance Issues**:
   - Check database indexes
   - Monitor system resources
   - Adjust batch sizes for large operations

### Support

For additional support or questions:
1. Check the logs in the terminal for detailed error messages
2. Verify all dependencies are properly installed
3. Ensure database connectivity and proper credentials
4. Review the MCP server configuration for Claude Desktop integration

## Next Steps

1. **Test with Sample Data**: Upload some test resumes to verify functionality
2. **Create Job Postings**: Add job positions to test matching algorithms
3. **Explore Analytics**: Review the dashboard and analytics features
4. **Customize Settings**: Adjust parameters based on your organization's needs
5. **Scale Testing**: Test with larger datasets to verify performance

The system is now ready for production use and can handle enterprise-scale recruitment operations efficiently!
