<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Enterprise Recruitment Agent - Copilot Instructions

This is an enterprise-level AI recruitment agent built with Python and the Model Context Protocol (MCP). The system is designed to handle large volumes of resumes (1000+) efficiently with advanced automation and matching capabilities.

## Project Overview

The Enterprise Recruitment Agent is a comprehensive recruitment automation system that includes:

- **Bulk Resume Processing**: Handle 1000+ resumes with parallel processing
- **AI-Powered Matching**: Advanced candidate-job matching using semantic analysis
- **Automated Screening**: Rule-based and AI-driven candidate screening
- **Interview Scheduling**: Automated interview scheduling with calendar integration
- **Analytics Dashboard**: Comprehensive recruitment metrics and insights
- **Workflow Automation**: End-to-end recruitment process automation

## Architecture

### Core Modules:

1. **server.py**: Main MCP server with tool definitions and handlers
2. **models.py**: Data models and type definitions
3. **database.py**: Database management with PostgreSQL and connection pooling
4. **resume_parser.py**: Advanced resume parsing with AI-powered extraction
5. **matching_engine.py**: Candidate-job matching algorithms
6. **bulk_processor.py**: High-performance bulk operations
7. **analytics.py**: Reporting and analytics engine
8. **automation.py**: Workflow automation and scheduling

### Key Features:

- **High Performance**: Optimized for 1000+ resume processing
- **Scalable Architecture**: Async/await patterns with connection pooling
- **Advanced Matching**: Semantic similarity and skill relationship matching
- **Enterprise Grade**: Comprehensive error handling and logging
- **Automation**: End-to-end workflow automation
- **Analytics**: Real-time dashboards and reporting

## Development Guidelines

### Code Style:
- Use async/await for all database operations
- Follow type hints for all function parameters and returns
- Use dataclasses for structured data
- Implement comprehensive error handling
- Add logging for all major operations

### Database Design:
- Use PostgreSQL with proper indexing for performance
- Implement batch operations for bulk data handling
- Use JSONB for flexible schema fields (skills, certifications)
- Maintain referential integrity with foreign keys

### Performance Considerations:
- Use connection pooling for database operations
- Implement parallel processing for bulk operations
- Use proper indexing for frequently queried fields
- Batch database operations when possible
- Implement caching for frequently accessed data

### MCP Integration:
- All tools should return formatted text responses
- Use proper error handling and return meaningful error messages
- Implement comprehensive tool descriptions and input schemas
- Support both individual and bulk operations

## Common Patterns

### Database Queries:
```python
async with self.db_manager.get_connection() as conn:
    query = "SELECT * FROM table WHERE condition = $1"
    result = await conn.fetch(query, param)
```

### Bulk Processing:
```python
# Process in batches for performance
batch_size = 50
for i in range(0, len(items), batch_size):
    batch = items[i:i + batch_size]
    await process_batch(batch)
```

### Error Handling:
```python
try:
    result = await operation()
    return [types.TextContent(type="text", text=f"✅ Success: {result}")]
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]
```

## Testing

- Use pytest with async support
- Test both individual operations and bulk processing
- Mock external dependencies (database, file operations)
- Test error conditions and edge cases

## Deployment

- Use environment variables for configuration
- Implement proper logging and monitoring
- Use database migrations for schema changes
- Implement health checks and performance monitoring

You can find more info and examples at https://modelcontextprotocol.io/llms-full.txt
You can find the MCP SDK documentation at https://github.com/modelcontextprotocol/create-python-server
