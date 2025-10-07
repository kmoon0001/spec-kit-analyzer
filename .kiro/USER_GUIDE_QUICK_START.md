# Quick Start Guide - Therapy Compliance Analyzer

## 🚀 Getting Started

### Login
- **Username**: `admin`
- **Password**: `admin123`

## 📋 New Layout Overview

### Left Column - Document & Rubric
1. **📁 Upload Document**
   - Click "Upload Document" button
   - Select PDF, DOCX, or TXT file
   - File name displays below

2. **📚 Select Rubric**
   - Choose from dropdown:
     - Medicare Policy Manual
     - Part B Guidelines
     - Custom rubrics

3. **Action Buttons**
   - ▶️ Run Analysis
   - 🔄 Repeat Analysis
   - 📄 View Full Report

### Middle Column - Settings & Sections
1. **⚙️ Review Strictness** (Top)
   - 😊 Lenient
   - 📋 Standard (recommended)
   - 🔍 Strict
   - Click to select

2. **📋 Report Sections** (Bottom)
   - Check/uncheck sections to include:
     - Executive Summary
     - Detailed Findings
     - Risk Assessment
     - Recommendations
     - Regulatory Citations
     - Action Plan
     - AI Transparency
     - Improvement Strategies

3. **Export Buttons**
   - 📄 PDF - Export as PDF
   - 🌐 HTML - Export as HTML

### Right Column - Results & Chat
1. **Analysis Results** (Top)
   - 📊 Summary tab - Quick overview
   - 📋 Details tab - Full analysis

2. **💬 Chat Bar** (Bottom)
   - Type questions about analysis
   - Click "Send" or press Enter
   - AI responds with context

## 🎯 Quick Workflow

### Running an Analysis
1. Upload your document (left column)
2. Select rubric (left column)
3. Choose strictness level (middle column, top)
4. Select report sections (middle column, bottom)
5. Click "▶️ Run Analysis" (left column)
6. Wait for results (30-60 seconds)
7. View results in right column
8. Ask questions in chat bar

### Exporting Reports
1. Complete an analysis
2. Go to middle column
3. Click "📄 PDF" or "🌐 HTML"
4. Choose save location
5. Report saved!

### Using Chat
1. Complete an analysis
2. Type question in chat bar (bottom right)
3. Click "Send"
4. Chat dialog opens with context
5. Get AI assistance

## 🎨 Visual Features

### Modern Tabs
- **Analysis** - Main workspace
- **Dashboard** - Historical trends
- **Mission Control** - System monitoring
- **Settings** - Preferences

### Color Coding
- **Blue** (#4a90e2) - Primary actions, selected items
- **White** - Input fields, active areas
- **Gray** - Borders, inactive items
- **Green** - Success messages
- **Red** - Errors, warnings

### Responsive Design
- Resize window - layout adapts
- Minimum size: 900x600
- Scales to larger screens
- No content cut off

## ⚙️ Settings Tab

### User Preferences
- Theme (Light/Dark)
- Account settings
- UI customization

### Analysis Settings
- 7 Habits integration
- Educational content
- Confidence scores
- Fact-checking
- Risk scoring
- Habit mapping
- NLG recommendations

### Report Settings
- Toggle report sections
- Customize output

### Performance Settings
- Caching
- Parallel processing
- Auto-cleanup
- Cache size
- Worker threads

## 💡 Tips & Tricks

### Keyboard Shortcuts
- `Ctrl+O` - Upload document
- `Ctrl+R` - Run analysis
- `Ctrl+E` - Export report
- `Ctrl+Q` - Quit application

### Best Practices
1. Use **Standard** strictness for balanced analysis
2. Enable all report sections for comprehensive output
3. Export PDF for professional documentation
4. Use chat for clarification on findings
5. Check Dashboard for trends over time

### Troubleshooting
- **Analysis hangs**: Check API server is running
- **PDF export fails**: Install weasyprint (`pip install weasyprint`)
- **Slow performance**: Adjust worker threads in Settings
- **Chat not working**: Ensure API server is running

## 📊 Understanding Results

### Summary Tab
- Overall compliance score
- Key findings count
- Risk distribution
- Quick recommendations

### Details Tab
- Full analysis report
- Evidence with citations
- Detailed recommendations
- Regulatory references

### Chat Integration
- Ask about specific findings
- Request clarification
- Get additional guidance
- Explore compliance topics

## 🎓 Learning Resources

### In-App Help
- Menu → Help → User Guide
- Menu → Help → Compliance Resources
- Menu → Help → About

### Documentation
- See `.kiro/steering/` folder
- WORKFLOW.md - Complete workflow
- testing_guide.md - Testing procedures
- user story.md - Feature descriptions

## 🔒 Security & Privacy

### Local Processing
- All AI runs on your computer
- No data sent to external servers
- HIPAA compliant
- PHI automatically scrubbed

### Data Storage
- Local SQLite database
- Encrypted sensitive data
- Automatic cleanup
- Secure file handling

## 📞 Support

### Getting Help
1. Check this guide first
2. Review documentation in `.kiro/steering/`
3. Check error messages for guidance
4. Use chat for AI assistance

### Common Issues
- **API not running**: Start with `python scripts/run_api.py`
- **Models not loaded**: Wait for initial download (~500MB)
- **Window too small**: Resize to at least 900x600
- **Export fails**: Check file permissions

## 🎉 Enjoy!

The Therapy Compliance Analyzer is designed to make compliance analysis easy and efficient. Explore the features, customize settings, and let AI help you improve documentation quality!

---

*Version 1.1.0 - October 6, 2025*
*Happy Analyzing! 🏥✨*
