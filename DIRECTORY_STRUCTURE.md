# Directory Structure

This document outlines the organized directory structure of the Therapy Compliance Analyzer project.

## 📁 Root Directory Structure

```
├── 📂 src/                    # Main source code
├── 📂 tests/                  # Test files and test suites
├── 📂 docs/                   # All project documentation
├── 📂 scripts/                # Utility and maintenance scripts
├── 📂 config/                 # Configuration files
├── 📂 database/               # Database files
├── 📂 test_data/              # Test documents and sample data
├── 📂 data/                   # Application data
├── 📂 logs/                   # Log files (when not in use)
├── 📂 wheels/                 # Python wheel packages
├── 📂 tools/                  # Development tools
├── 📄 README.md               # Main project documentation
├── 📄 requirements*.txt       # Python dependencies
├── 📄 .env                    # Environment variables
└── 📄 .gitignore              # Git ignore rules
```

## 📂 Folder Descriptions

### `/src/` - Source Code
Contains the main application code:
- API backend (FastAPI)
- GUI frontend (PyQt6)
- Core business logic
- Database models and schemas

### `/tests/` - Test Suite
All testing files:
- Unit tests
- Integration tests
- GUI tests
- Test fixtures and utilities

### `/docs/` - Documentation
All project documentation files:
- Feature specifications
- Implementation guides
- Performance reports
- Security documentation
- User guides

### `/scripts/` - Utility Scripts
Maintenance and utility scripts:
- Database initialization
- Feature validation
- Import checking
- Diagnostic tools

### `/config/` - Configuration
Configuration files:
- Application config (YAML)
- Performance settings (JSON)
- Testing configuration (INI)

### `/database/` - Database Files
SQLite database files:
- Main database
- Database journals and WAL files

### `/test_data/` - Test Data
Sample documents and test files:
- Therapy notes
- Test documents
- Sample reports

### `/wheels/` - Python Packages
Custom Python wheel packages:
- Specialized NLP models
- Custom dependencies

## 🧹 Cleanup Benefits

This organization provides:
- **Clear separation of concerns**
- **Easy navigation and maintenance**
- **Better version control**
- **Simplified deployment**
- **Improved development workflow**

## 🔍 Finding Files

- **Source code**: Look in `/src/`
- **Documentation**: Check `/docs/`
- **Scripts**: Find in `/scripts/`
- **Configuration**: Located in `/config/`
- **Test files**: Available in `/test_data/`

---

*This structure follows Python project best practices and makes the codebase more maintainable.*