---
inclusion: always
---

# Product Guidelines

## Therapy Compliance Analyzer

AI-powered desktop application for clinical therapists to analyze documentation for compliance with Medicare and regulatory guidelines. All processing occurs locally for data privacy.

## Core Product Principles

### Privacy & Security First
- All AI/ML processing must happen locally - never send data to external APIs
- Use JWT authentication with secure token handling
- Implement proper data sanitization (PHI scrubbing)
- Store sensitive data encrypted at rest

### Medical Domain Expertise
- Use specialized biomedical NER models for accurate entity extraction
- Implement medical terminology validation and standardization
- Provide clear uncertainty indicators for AI-generated insights
- Include medical disclaimers and AI limitation disclosures

### User Experience Standards
- Design for clinical workflow integration
- Provide clear, actionable compliance feedback
- Use progressive disclosure for complex analysis results
- Implement responsive UI that handles long-running AI operations

## Feature Development Guidelines

### Document Analysis Features
- Support multiple formats: PDF, DOCX, TXT
- Implement hybrid search (semantic + keyword matching)
- Provide detailed compliance scoring with explanations
- Generate exportable compliance reports

### Dashboard & Analytics
- Show historical compliance trends
- Highlight recurring compliance issues
- Provide drill-down capabilities for detailed analysis
- Support filtering by date ranges, document types, compliance areas

### Rubric Management
- Allow custom compliance rule creation
- Support TTL format for structured rubrics
- Enable rule versioning and change tracking
- Provide rule testing and validation tools

## Code Quality Standards

### Error Handling
- Gracefully handle AI model failures
- Provide meaningful error messages for users
- Implement retry logic for transient failures
- Log errors appropriately without exposing PHI

### Performance Requirements
- Optimize for local processing constraints
- Implement progress indicators for long operations
- Use background processing for non-blocking UI
- Cache frequently accessed data appropriately

### Testing Standards
- Write tests that don't require real PHI data
- Mock external dependencies and AI models
- Test error conditions and edge cases
- Include GUI interaction testing with pytest-qt

## Domain-Specific Considerations

### Compliance Terminology
- Use standard healthcare compliance terminology
- Reference Medicare guidelines and CMS requirements
- Implement proper medical coding validation
- Support multiple regulatory frameworks

### Clinical Workflow Integration
- Design for typical therapist documentation patterns
- Support batch processing of multiple documents
- Provide quick compliance checks during documentation
- Enable integration with existing clinical systems