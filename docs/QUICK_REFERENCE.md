# Quick Reference Guide - Therapy Compliance Analyzer

## 🚀 Launch
```bash
python start_app.py
```

## 📋 Main Interface

### Tabs
- **📋 Analysis** - Main workspace
- **📊 Dashboard** - Analytics and trends
- **📄 Reports** - Export and reporting
- **⚙️ Admin** - Administration (admin only)

### Key Buttons
| Button | Function | Location |
|--------|----------|----------|
| 🔍 Run Analysis | Start compliance check | Analysis tab |
| ⏹️ Stop | Cancel analysis | Analysis tab |
| 💬 AI Chat | Open chat assistant | Analysis tab / Tools menu |
| 📥 Export Report | Save as PDF/HTML | Analysis tab / File menu |
| 🗑️ Clear | Reset workspace | Analysis tab |
| 📄 Upload Document | Load file | Analysis tab / File menu |
| 📁 Upload Folder | Batch upload | Analysis tab / File menu |

## 🍔 Menu Bar Quick Access

### File Menu (📁)
- Upload Document
- Upload Folder
- Export Report (PDF)
- Export Report (HTML)
- Exit

### Tools Menu (🔧)
- **AI Chat Assistant** ← Most used!
- Manage Rubrics
- Performance Settings
- Change Password

### View Menu (👁️)
- Light Theme
- Dark Theme
- Document Preview

### Admin Menu (⚙️)
- User Management
- System Settings
- Audit Logs
- Team Analytics
- Database Maintenance

### Help Menu (❓)
- Documentation
- Compliance Guidelines
- About

## 🏥 Disciplines

### Select Your Discipline
1. **Physical Therapy (PT)** - Index 0
2. **Occupational Therapy (OT)** - Index 1
3. **Speech-Language Pathology (SLP)** - Index 2

### Compliance Rules by Discipline

#### PT Rules (5 rules, $265 total impact)
- Signature/date ($50)
- Measurable goals ($50)
- Medical necessity ($50)
- Skilled services ($75)
- Progress documentation ($40)

#### OT Rules (5 rules, $225 total impact)
- Signature/date ($50)
- OT goals (ADLs) ($50)
- Medical necessity ($50)
- COTA supervision ($25)
- Plan of care ($50)

#### SLP Rules (5 rules, $275 total impact)
- Signature/date ($50)
- SLP Plan of Care ($60)
- Skilled SLP justification ($75)
- Measurable SLP goals ($50)
- Progress reports ($40)

## 💬 AI Chat Assistant

### How to Open
- Click "💬 AI Chat" button in Analysis tab
- Or: Tools menu → AI Chat Assistant

### What to Ask
- "How do I write measurable goals?"
- "What is medical necessity?"
- "Why is my signature missing?"
- "Explain this finding"
- "Documentation tips for PT/OT/SLP"

### Sample Questions
```
User: "How do I document medical necessity?"
AI: "Medical necessity means documenting why skilled therapy 
     is required. Link interventions to functional limitations..."

User: "What are SMART goals?"
AI: "Goals should be Specific, Measurable, Achievable, 
     Relevant, and Time-bound. Example: 'Patient will 
     increase right shoulder flexion from 90° to 120° 
     within 3 weeks...'"
```

## 📊 Understanding Your Score

### Score Ranges
- **90-100%** 🟢 Excellent - Audit ready
- **80-89%** 🟢 Good - Minor improvements
- **70-79%** 🟡 Fair - Address issues
- **60-69%** 🟡 Poor - Significant work needed
- **0-59%** 🔴 Critical - Major revision required

### Score Calculation
```
Score = 100 - (Total Financial Impact / Total Possible Impact × 100)
```

Example:
- Total possible impact: $265 (PT)
- Your findings: $100
- Score: 100 - (100/265 × 100) = 62.3%

## 📄 Reports

### Generate Report
1. Run analysis
2. Click "📥 Export Report"
3. Choose format (PDF or HTML)
4. Select save location

### Report Contents
- Compliance score
- Discipline
- Financial risk
- Findings table
- Suggestions

## 🔧 Common Tasks

### Analyze a Document
```
1. Select discipline (PT/OT/SLP)
2. Click "Upload Document"
3. Choose file
4. Click "Run Analysis"
5. Review results
```

### Export Results
```
1. Complete analysis
2. Click "Export Report"
3. Choose PDF or HTML
4. Save file
```

### Ask AI for Help
```
1. Click "AI Chat" button
2. Type your question
3. Click "Send Message"
4. Read AI response
```

### Clear and Start Over
```
1. Click "Clear" button
2. Upload new document
3. Run new analysis
```

## ⚙️ Admin Tasks

### User Management
```
Admin menu → User Management
- Add new users
- Edit permissions
- Delete accounts
```

### View Team Analytics
```
Admin menu → Team Analytics
- Organization metrics
- User comparisons
- Trend analysis
```

### Database Maintenance
```
Admin menu → Database Maintenance
- Cleanup old data
- Optimize performance
- Backup database
```

## 🎨 Customization

### Change Theme
```
View menu → Light Theme / Dark Theme
```

### Performance Settings
```
Tools menu → Performance Settings
- Adjust cache size
- Set memory limits
- Configure workers
```

## 🐛 Troubleshooting

### Analysis Not Starting
- Check document is loaded
- Verify discipline selected
- Ensure text area not empty

### No Results Showing
- Wait for analysis to complete
- Check progress bar
- Look for error messages

### Chat Not Responding
- Verify chat window is open
- Check message was sent
- Try reopening chat

### Export Failing
- Run analysis first
- Check file permissions
- Verify save location exists

## 📞 Support

### Get Help
- Help menu → Documentation
- Help menu → Compliance Guidelines
- Help menu → About

### Report Issues
- Check error messages
- Review audit logs (admin)
- Contact support

## 🎯 Best Practices

### Before Analysis
✅ Select correct discipline
✅ Upload complete documentation
✅ Review document for obvious errors

### During Analysis
✅ Wait for completion
✅ Monitor progress bar
✅ Don't close application

### After Analysis
✅ Review all findings
✅ Use AI chat for clarification
✅ Export report for records
✅ Update documentation
✅ Re-analyze to verify

## 📈 Keyboard Shortcuts (Coming Soon)

- `Ctrl+O` - Upload Document
- `Ctrl+R` - Run Analysis
- `Ctrl+E` - Export Report
- `Ctrl+Q` - AI Chat
- `Ctrl+W` - Clear
- `Ctrl+S` - Save Report

---

## 🎓 Quick Tips

1. **Always select discipline first** - PT, OT, or SLP
2. **Use AI chat liberally** - It's there to help!
3. **Export reports regularly** - Keep records
4. **Aim for 80%+ scores** - Good compliance threshold
5. **Address HIGH severity first** - Biggest financial impact
6. **Review suggestions carefully** - Specific to your discipline
7. **Use dashboard for trends** - Track improvement over time

---

**Need more help?** Check `COMPLETE_FEATURES_LIST.md` for detailed feature documentation!
