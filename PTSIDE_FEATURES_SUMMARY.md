# PTside - Feature Summary & User Guide

## 🏃‍♂️ What is PTside?

PTside is a streamlined Physical Therapy compliance analyzer that helps PT professionals ensure their documentation meets Medicare Part B requirements. It's a focused, standalone tool that provides instant feedback on compliance issues.

## ✨ Key Features

### 1. Main Analysis Interface

**Left Panel - Document Input**
- 📄 Large text area for entering PT documentation
- Pre-loaded with a sample PT progress note
- Supports copy/paste from your EHR system
- Clear placeholder text with PT documentation guidelines

**Right Panel - Results Display**
- 📊 Compliance score progress bar (0-100%)
- Color-coded scoring:
  - 🟢 Green (80-100%): Good compliance
  - 🟡 Yellow (60-79%): Needs improvement
  - 🔴 Red (0-59%): Significant issues
- Detailed findings table with 4 columns:
  - Issue description
  - Severity level (HIGH/MEDIUM)
  - Financial impact ($)
  - PT-specific suggestions

**Bottom Panel - PT Analysis**
- PT credentials verification
- Intervention count
- Objective measurements count
- Functional terminology usage
- Key interventions found
- Measurements documented

### 2. Buttons & Controls

| Button | Function | Location |
|--------|----------|----------|
| 🔍 Analyze PT Compliance | Runs compliance analysis | Bottom of left panel |
| 📋 PT Compliance Analysis (tab) | Main analysis interface | Top tab bar |
| 📚 PT Guidelines (tab) | Reference documentation | Top tab bar |

### 3. PT Compliance Rules Checked

#### HIGH Severity Issues
1. **Missing Signature/Date** ($50 impact)
   - Checks for: signature, signed, dated, therapist, PT, by
   
2. **Medical Necessity Not Documented** ($50 impact)
   - Checks for: medical necessity, functional limitation, skilled therapy
   
3. **Plan of Care Not Referenced** ($50 impact)
   - Checks for: plan of care, POC, certification, physician order
   
4. **Skilled Services Not Documented** ($75 impact)
   - Checks for: skilled, therapeutic exercise, manual therapy, gait training

#### MEDIUM Severity Issues
1. **Goals Not Measurable/Time-bound** ($50 impact)
   - Checks for goals with measurable criteria and timeframes
   
2. **Assistant Supervision Unclear** ($25 impact)
   - Checks for proper supervision documentation when PTAs involved
   
3. **Progress Not Documented** ($40 impact)
   - Checks for: progress, improvement, response to treatment

### 4. PT-Specific Pattern Detection

**Automatically Detects:**
- PT credentials (PT, DPT, Physical Therapist)
- PT interventions (therapeutic exercise, manual therapy, gait training, balance, ROM)
- Objective measurements (degrees, reps, sets, minutes, feet, lbs)
- Functional terms (ADL, ambulation, transfers, mobility)

### 5. Guidelines Reference Tab

**Comprehensive PT Documentation Guide:**
- Required documentation elements
- PT-specific interventions to document
- Common compliance issues
- Financial impact of non-compliance
- Best practices for PT documentation

## 🚀 How to Use PTside

### Quick Start

1. **Launch the application**
   ```bash
   python start_app.py
   ```

2. **Enter your PT documentation**
   - Copy/paste from your EHR
   - Or type directly into the text area
   - Sample note is pre-loaded for testing

3. **Click "🔍 Analyze PT Compliance"**
   - Analysis runs instantly (no waiting!)
   - Results appear in the right panel

4. **Review findings**
   - Check your compliance score
   - Read each finding in the table
   - Note the financial impact
   - Follow the PT-specific suggestions

5. **Reference guidelines**
   - Click "📚 PT Guidelines" tab
   - Review Medicare requirements
   - Learn best practices

### Example Workflow

```
1. Copy PT progress note from EHR
2. Paste into PTside document area
3. Click Analyze button
4. Review compliance score (e.g., 75%)
5. Check findings table:
   - Missing signature → Add signature/date
   - Goals not measurable → Revise to SMART goals
   - Medical necessity unclear → Add functional justification
6. Update your documentation
7. Re-analyze to verify improvements
8. Achieve 90%+ compliance score!
```

## 💡 Tips for Best Results

### Documentation Best Practices

1. **Always Include:**
   - Patient name, DOB, diagnosis
   - Date of service
   - Skilled PT interventions performed
   - Objective measurements (ROM, strength, distance)
   - Progress toward goals
   - Medical necessity justification
   - Therapist signature with credentials

2. **Use SMART Goals:**
   - ❌ Bad: "Patient will improve strength"
   - ✅ Good: "Patient will increase right quad strength from 3/5 to 4/5 within 2 weeks to improve stair climbing"

3. **Document Medical Necessity:**
   - Link interventions to functional limitations
   - Explain why skilled PT is required
   - Reference physician orders

4. **Include Objective Measures:**
   - ROM in degrees
   - Strength grades (0/5 to 5/5)
   - Distances ambulated
   - Repetitions/sets performed
   - Time durations

## 🎯 Understanding Your Score

### Score Interpretation

- **90-100%**: Excellent compliance
  - All key elements present
  - Minimal denial risk
  - Ready for audit

- **80-89%**: Good compliance
  - Most elements present
  - Minor improvements needed
  - Low denial risk

- **70-79%**: Fair compliance
  - Some key elements missing
  - Moderate denial risk
  - Address high-severity issues

- **60-69%**: Poor compliance
  - Multiple elements missing
  - High denial risk
  - Immediate action required

- **Below 60%**: Critical issues
  - Major compliance gaps
  - Very high denial risk
  - Comprehensive revision needed

## 🔧 Troubleshooting

### Common Issues

**Q: Score seems too low?**
A: Check that you included:
- Signature and date
- Medical necessity statement
- Measurable goals with timeframes
- Skilled intervention descriptions

**Q: Not detecting my PT credentials?**
A: Make sure you include "PT", "DPT", or "Physical Therapist" in your note

**Q: Want to test with different notes?**
A: Clear the text area and paste your own documentation, or modify the sample note

## 📊 Financial Impact Guide

Understanding the dollar amounts:

- **$75**: Skilled services not documented (highest risk)
- **$50**: Missing signature, medical necessity, goals, plan of care
- **$40**: Progress not documented
- **$25**: Assistant supervision unclear

**Total Possible Impact**: $335 per visit if all issues present

## 🎓 Learning Resources

The Guidelines tab includes:
- Medicare Part B requirements
- PT-specific intervention examples
- Common compliance pitfalls
- Best practice recommendations
- Financial impact explanations

## 🚀 Future Enhancements (Planned)

- File upload button for loading saved notes
- Export button for saving analysis results
- OT and SLP discipline tabs
- Custom rule configuration
- Historical tracking of compliance scores
- Batch analysis for multiple notes

## ✅ Success Checklist

Before submitting documentation:
- [ ] Compliance score 80% or higher
- [ ] All HIGH severity issues resolved
- [ ] Signature and date present
- [ ] Medical necessity documented
- [ ] Goals are SMART (measurable, time-bound)
- [ ] Skilled interventions described
- [ ] Progress documented
- [ ] Plan of care referenced

---

**PTside** - Making PT compliance simple and transparent! 🏃‍♂️
