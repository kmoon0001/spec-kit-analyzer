# 7 Habits Framework - Settings Guide

## Overview

The 7 Habits Personal Development Framework is a fully configurable feature that can be customized to match your organization's preferences and workflow. All settings are controlled through `config.yaml`.

## Master Toggle

```yaml
habits_framework:
  enabled: true  # Turn entire feature on/off
```

**When disabled:** All habit-related features are hidden from reports, dashboard, and UI.

---

## Visibility Levels

Choose how prominent the habits feature should be:

```yaml
habits_framework:
  visibility_level: "moderate"  # Options: "subtle", "moderate", "prominent"
```

### Visibility Level Comparison

| Feature | Subtle (A) | Moderate (B) ⭐ | Prominent (C) |
|---------|-----------|----------------|---------------|
| **Habit tags on findings** | Small icon only | Visible tag with name | Large, colorful badge |
| **Personal Development section** | Hidden by default | Collapsed by default | Expanded by default |
| **Habit tooltips** | On hover only | On hover with preview | Always visible |
| **Dashboard habits tab** | Not shown | Shown as optional tab | Shown prominently |
| **Weekly focus widget** | Not shown | Small widget | Large featured widget |
| **Notifications** | None | Milestones only | All achievements |

**Recommended:** `"moderate"` - Provides value without overwhelming users

---

## Report Integration Settings

Control how habits appear in compliance reports:

```yaml
habits_framework:
  report_integration:
    show_habit_tags: true              # Show habit tags on findings
    show_personal_development_section: true  # Show collapsible section
    show_habit_tooltips: true          # Show hover tooltips
    habit_section_expanded_by_default: false  # Start collapsed
```

### Examples

**Moderate Visibility (Default):**
```
Finding: Missing objective measurements
Risk: HIGH | Confidence: 92%

💡 Habit 2: Begin with the End in Mind
   [Hover for quick tips]

[Personal Development Insights] ▼ Click to expand
```

**Prominent Visibility:**
```
Finding: Missing objective measurements
Risk: HIGH | Confidence: 92%

🎯 HABIT 2: BEGIN WITH THE END IN MIND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This finding relates to having clear, measurable goals.

Quick Tips:
• Use SMART goal framework
• Document functional outcomes
• Include discharge criteria

[View detailed strategies →]

[Personal Development Insights] ▼ Expanded by default
```

---

## Dashboard Integration Settings

Control habits features in the analytics dashboard:

```yaml
habits_framework:
  dashboard_integration:
    show_growth_journey_tab: true      # Dedicated habits tab
    show_weekly_focus_widget: true     # "This Week's Focus" widget
    show_habit_progression_charts: true  # Mastery visualizations
    show_peer_comparison: false        # Anonymous benchmarking
```

### Dashboard Features

**Growth Journey Tab:**
- Habit progression over time
- Mastery level tracking
- Personalized coaching recommendations
- Achievement history

**Weekly Focus Widget:**
- AI-generated weekly habit focus
- Progress tracking
- Quick action items

**Habit Progression Charts:**
- Visual mastery levels
- Trend analysis
- Improvement tracking

**Peer Comparison (Optional):**
- Anonymous benchmarking
- Percentile rankings
- Best practice insights

---

## AI-Powered Features

Enable advanced AI capabilities:

```yaml
habits_framework:
  ai_features:
    use_ai_mapping: false              # AI contextual habit mapping
    use_ai_coaching: false             # AI habit coach assistant
    personalized_strategies: true      # Custom improvement tips
```

### AI Features Explained

**AI Mapping:**
- Uses LLM to understand finding context
- More accurate habit assignment
- Considers document type and discipline
- **Requires:** LLM service running

**AI Coaching:**
- Interactive habit coach chatbot
- Personalized guidance
- Answers habit-related questions
- **Requires:** LLM service running

**Personalized Strategies:**
- Generates custom improvement tips
- Based on individual patterns
- Tailored to discipline and document type
- **Works without LLM** (uses templates)

---

## Gamification & Motivation

Control achievement and motivation features:

```yaml
habits_framework:
  gamification:
    enabled: true                      # Enable achievement system
    show_badges: true                  # Show achievement badges
    show_streaks: true                 # Show improvement streaks
    show_milestones: true              # Celebrate milestones
    notifications_enabled: false       # Achievement notifications
```

### Gamification Elements

**Badges:**
- Habit mastery achievements
- Milestone celebrations
- Professional, not childish

**Streaks:**
- Consecutive days without findings
- Improvement tracking
- Motivational feedback

**Milestones:**
- 10, 50, 100 analyses
- Habit mastery levels
- Compliance improvements

**Notifications:**
- Off by default (non-intrusive)
- Weekly summaries only
- No pop-ups or interruptions

---

## Educational Content

Control learning resources:

```yaml
habits_framework:
  education:
    show_habit_resources: true         # Detailed explanations
    show_clinical_examples: true       # Clinical applications
    show_improvement_strategies: true  # Actionable strategies
    show_templates: true               # Documentation templates
```

### Educational Resources

**Habit Resources:**
- Complete habit descriptions
- Covey's principles explained
- Clinical applications

**Clinical Examples:**
- Real-world scenarios
- Best practices
- Common pitfalls

**Improvement Strategies:**
- Step-by-step guides
- Actionable tips
- Quick wins

**Templates:**
- Habit-based documentation templates
- Checklists
- Quick reference guides

---

## Privacy & Data Settings

Control data collection and sharing:

```yaml
habits_framework:
  privacy:
    track_progression: true            # Track improvement over time
    anonymous_analytics: true          # Contribute to benchmarks
    share_achievements: false          # Social sharing
```

### Privacy Considerations

**Track Progression:**
- Stores habit metrics locally
- Enables trend analysis
- Required for mastery tracking

**Anonymous Analytics:**
- Contributes to peer benchmarks
- No PHI or identifying information
- Helps improve the system

**Share Achievements:**
- Off by default
- Optional social sharing
- User-controlled

---

## Advanced Settings

Fine-tune the habits framework:

```yaml
habits_framework:
  advanced:
    habit_confidence_threshold: 0.6    # Min confidence for mapping
    focus_area_threshold: 0.20         # "Needs focus" threshold (20%)
    mastery_threshold: 0.05            # "Mastered" threshold (5%)
    weekly_focus_enabled: true         # Generate weekly focus
    auto_suggest_templates: true       # Suggest templates
```

### Advanced Settings Explained

**Habit Confidence Threshold:**
- Minimum confidence for habit assignment
- Lower = more habit assignments
- Higher = only high-confidence matches
- **Recommended:** 0.6 (60%)

**Focus Area Threshold:**
- Percentage of findings to trigger "needs focus"
- If habit represents >20% of findings, flag it
- **Recommended:** 0.20 (20%)

**Mastery Threshold:**
- Percentage of findings to consider "mastered"
- If habit represents <5% of findings, mastered
- **Recommended:** 0.05 (5%)

**Weekly Focus:**
- AI generates weekly habit focus
- Based on recent findings
- Personalized recommendations

**Auto-Suggest Templates:**
- Suggests templates based on findings
- Habit-specific documentation aids
- Proactive assistance

---

## Configuration Presets

### Preset 1: Minimal (Subtle)
```yaml
habits_framework:
  enabled: true
  visibility_level: "subtle"
  report_integration:
    show_habit_tags: true
    show_personal_development_section: false
    show_habit_tooltips: true
    habit_section_expanded_by_default: false
  dashboard_integration:
    show_growth_journey_tab: false
    show_weekly_focus_widget: false
    show_habit_progression_charts: false
    show_peer_comparison: false
  gamification:
    enabled: false
```

**Use case:** Organizations that want habits available but not prominent

---

### Preset 2: Balanced (Moderate) ⭐ RECOMMENDED
```yaml
habits_framework:
  enabled: true
  visibility_level: "moderate"
  report_integration:
    show_habit_tags: true
    show_personal_development_section: true
    show_habit_tooltips: true
    habit_section_expanded_by_default: false
  dashboard_integration:
    show_growth_journey_tab: true
    show_weekly_focus_widget: true
    show_habit_progression_charts: true
    show_peer_comparison: false
  gamification:
    enabled: true
    notifications_enabled: false
```

**Use case:** Most organizations - visible but not overwhelming

---

### Preset 3: Full Featured (Prominent)
```yaml
habits_framework:
  enabled: true
  visibility_level: "prominent"
  report_integration:
    show_habit_tags: true
    show_personal_development_section: true
    show_habit_tooltips: true
    habit_section_expanded_by_default: true
  dashboard_integration:
    show_growth_journey_tab: true
    show_weekly_focus_widget: true
    show_habit_progression_charts: true
    show_peer_comparison: true
  ai_features:
    use_ai_mapping: true
    use_ai_coaching: true
  gamification:
    enabled: true
    notifications_enabled: true
```

**Use case:** Organizations focused on professional development

---

## Changing Settings

### Method 1: Edit config.yaml (Recommended)

1. Open `config.yaml` in your editor
2. Find the `habits_framework` section
3. Modify settings as needed
4. Restart the application

### Method 2: Environment Variables

Override specific settings:
```bash
export HABITS_FRAMEWORK_ENABLED=false
export HABITS_FRAMEWORK_VISIBILITY_LEVEL=prominent
```

### Method 3: Settings UI (Future)

A settings management UI is planned for future releases.

---

## Testing Your Configuration

After changing settings, verify they work:

1. **Run an analysis** - Check if habit tags appear as expected
2. **View report** - Verify Personal Development section visibility
3. **Check dashboard** - Confirm habits tab presence
4. **Test tooltips** - Hover over habit tags

---

## Troubleshooting

### Habits not showing in reports
- Check `habits_framework.enabled: true`
- Verify `report_integration.show_habit_tags: true`
- Restart application after config changes

### AI features not working
- Ensure LLM service is running
- Check `ai_features.use_ai_mapping: true`
- Verify model is loaded successfully

### Dashboard tab missing
- Check `dashboard_integration.show_growth_journey_tab: true`
- Verify visibility_level is not "subtle"
- Clear browser cache if using web interface

---

## Best Practices

1. **Start with "moderate"** visibility - Adjust based on user feedback
2. **Enable AI features gradually** - Test with small group first
3. **Keep notifications off** - Less intrusive, better user experience
4. **Enable progression tracking** - Valuable for improvement insights
5. **Review settings quarterly** - Adjust based on usage patterns

---

## Support

For questions about habits framework settings:
- See `FEATURE_AUDIT_AND_ROADMAP.md` for feature details
- Check `src/core/enhanced_habit_mapper.py` for technical details
- Contact support for custom configuration assistance

---

**Last Updated:** 2025-01-01
**Version:** 1.0.0
