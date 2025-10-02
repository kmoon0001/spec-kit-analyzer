"""
Clinical Compliance Report Generator

Generates comprehensive HTML reports following the structure defined in REPORT_ELEMENTS.md.
Includes executive summary, detailed findings, AI transparency, and regulatory citations.
"""

import logging
import os
import urllib.parse
from datetime import UTC, datetime
from collections import Counter
from typing import Any, Dict, List, Optional

import markdown

from .enhanced_habit_mapper import SevenHabitsFramework
from .text_utils import sanitize_human_text
from ..config import get_settings

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ReportGenerator:
    """
    Generates comprehensive clinical compliance reports following REPORT_ELEMENTS.md structure.

    Produces HTML reports with executive summary, detailed findings table, AI transparency
    section, regulatory citations, and action planning recommendations.
    
    Now includes enhanced 7 Habits Personal Development Framework integration.
    """

    def __init__(self, llm_service=None):
        self.rubric_template_str = self._load_template(
            os.path.join(ROOT_DIR, "src", "resources", "report_template.html")
        )
        self.model_limitations_html = self._load_and_convert_markdown(
            os.path.join(ROOT_DIR, "src", "resources", "model_limitations.md")
        )
        
        # Initialize habits framework
        self.settings = get_settings()
        self.habits_enabled = self.settings.habits_framework.enabled
        
        if self.habits_enabled:
            use_ai = self.settings.habits_framework.ai_features.use_ai_mapping
            self.habits_framework = SevenHabitsFramework(
                use_ai_mapping=use_ai,
                llm_service=llm_service
            )
        else:
            self.habits_framework = None

    @staticmethod
    def _load_template(template_path: str) -> str:
        try:
            with open(template_path, "r", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            return "<h1>Report</h1><p>Template not found.</p><div>{findings}</div>"

    @staticmethod
    def _load_and_convert_markdown(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                md_text = handle.read()
            return markdown.markdown(md_text, extensions=["tables"])
        except (ImportError, FileNotFoundError):
            return "<p>Could not load model limitations document.</p>"

    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        *,
        document_name: str | None = None,
        analysis_mode: str = "rubric",
    ) -> Dict[str, Any]:
        """Build a normalized payload consumed by higher-level services."""
        doc_name = document_name or analysis_result.get("document_name", "Document")
        report_html = self.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode,
        )
        findings = analysis_result.get("findings", [])
        return {
            "analysis": analysis_result,
            "findings": findings,
            "summary": analysis_result.get("summary", ""),
            "report_html": report_html,
            "generated_at": datetime.now(tz=UTC).isoformat(),
        }

    def generate_html_report(
        self, analysis_result: dict, doc_name: str, analysis_mode: str = "rubric"
    ) -> str:
        """Generate HTML report based on analysis mode."""
        return self._generate_rubric_report(analysis_result, doc_name)

    def _generate_rubric_report(self, analysis_result: dict, doc_name: str) -> str:
        """Generate comprehensive rubric-based compliance report."""
        template_str = self.rubric_template_str

        # Basic report metadata
        report_html = self._populate_basic_metadata(
            template_str, doc_name, analysis_result
        )

        # Generate findings table
        findings = analysis_result.get("findings", [])
        findings_rows_html = self._generate_findings_table(findings, analysis_result)

        report_html = report_html.replace(
            "<!-- Placeholder for findings rows -->", findings_rows_html
        )

        report_html = self._inject_summary_sections(report_html, analysis_result)
        report_html = self._inject_checklist(
            report_html, analysis_result.get("deterministic_checks", [])
        )
        report_html = report_html.replace(
            "<!-- Placeholder for pattern analysis -->",
            self._build_pattern_analysis(analysis_result),
        )

        # Add AI transparency section
        report_html = report_html.replace(
            "<!-- Placeholder for model limitations -->", self.model_limitations_html
        )
        
        # Add Personal Development section (if habits enabled)
        if self.habits_enabled and self.settings.habits_framework.report_integration.show_personal_development_section:
            personal_dev_html = self._generate_personal_development_section(findings, analysis_result)
            report_html = report_html.replace(
                "<!-- Placeholder for personal development -->", personal_dev_html
            )
        else:
            report_html = report_html.replace(
                "<!-- Placeholder for personal development -->", ""
            )

        return report_html

    def _populate_basic_metadata(
        self, template_str: str, doc_name: str, analysis_result: dict
    ) -> str:
        """Populate basic report metadata and summary information."""
        report_html = template_str.replace(
            "<!-- Placeholder for document name -->", doc_name
        )

        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_html = report_html.replace(
            "<!-- Placeholder for analysis date -->", analysis_date
        )

        compliance_score = analysis_result.get("compliance_score", "N/A")
        report_html = report_html.replace(
            "<!-- Placeholder for compliance score -->", str(compliance_score)
        )

        findings_count = len(analysis_result.get("findings", []))
        report_html = report_html.replace(
            "<!-- Placeholder for total findings -->", str(findings_count)
        )

        doc_type = sanitize_human_text(analysis_result.get("document_type", "Unknown"))
        discipline = sanitize_human_text(analysis_result.get("discipline", "Unknown"))
        report_html = report_html.replace(
            "<!-- Placeholder for document type -->", doc_type
        )
        report_html = report_html.replace(
            "<!-- Placeholder for discipline -->", discipline
        )

        overall_confidence = analysis_result.get("overall_confidence")
        if isinstance(overall_confidence, (int, float)):
            confidence_text = f"{overall_confidence:.0%}"
        else:
            confidence_text = "Not reported"
        report_html = report_html.replace(
            "<!-- Placeholder for overall confidence -->", confidence_text
        )

        return report_html

    def _generate_findings_table(self, findings: list, analysis_result: dict = None) -> str:
        """Generate the detailed findings analysis table."""
        if not findings:
            return '<tr><td colspan="6">No compliance findings identified.</td></tr>'

        findings_rows_html = ""
        for finding in findings:
            # Determine row styling based on confidence and dispute status
            row_class = self._get_finding_row_class(finding)

            # Generate table cells
            risk_cell = self._generate_risk_cell(finding)
            text_cell = self._generate_text_cell(finding)
            issue_cell = self._generate_issue_cell(finding, analysis_result)
            recommendation_cell = self._generate_recommendation_cell(finding)
            prevention_cell = self._generate_prevention_cell(finding, analysis_result)
            confidence_cell = self._generate_confidence_cell(finding)

            findings_rows_html += f"""
            <tr {row_class}>
                <td>{risk_cell}</td>
                <td>{text_cell}</td>
                <td>{issue_cell}</td>
                <td>{recommendation_cell}</td>
                <td>{prevention_cell}</td>
                <td>{confidence_cell}</td>
            </tr>
            """

        return findings_rows_html

    def _get_finding_row_class(self, finding: dict) -> str:
        """Determine CSS class for finding row based on confidence and status."""
        if finding.get("is_disputed"):
            return 'class="disputed"'

        confidence = finding.get("confidence", 0)
        if isinstance(confidence, (int, float)):
            if confidence >= 0.8:
                return 'class="high-confidence"'
            elif confidence >= 0.6:
                return 'class="medium-confidence"'
            else:
                return 'class="low-confidence"'

        if finding.get("is_low_confidence"):
            return 'class="low-confidence"'

        return ""

    def _generate_risk_cell(self, finding: dict) -> str:
        """Generate risk level cell with appropriate styling."""
        risk = sanitize_human_text(finding.get("risk", "Unknown").upper())
        risk_class = f"risk-{risk.lower()}" if risk in ["HIGH", "MEDIUM", "LOW"] else ""

        risk_html = f'<span class="{risk_class}">{risk}</span>'

        # Add financial impact if available
        financial_impact = finding.get("financial_impact")
        if financial_impact:
            risk_html += f"<br><small>Impact: {financial_impact}</small>"

        return risk_html

    def _generate_text_cell(self, finding: dict) -> str:
        """Generate problematic text cell with highlighting link."""
        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        context_snippet = sanitize_human_text(
            finding.get("context_snippet", problematic_text)
        )

        # Create highlight link for source document navigation
        combined_payload = f"{context_snippet}|||{problematic_text}"
        encoded_payload = urllib.parse.quote(combined_payload)

        return f'<a href="highlight://{encoded_payload}" class="highlight-link">{problematic_text}</a>'

    def _generate_issue_cell(self, finding: dict, analysis_result: dict = None) -> str:
        """Generate compliance issue cell with regulatory citations and habit tags."""
        issue_title = sanitize_human_text(
            finding.get("issue_title", "Compliance Issue")
        )
        regulation = sanitize_human_text(finding.get("regulation", ""))

        issue_html = f"<strong>{issue_title}</strong>"

        if regulation:
            issue_html += f"<br><small><em>Citation: {regulation}</em></small>"

        # Add severity justification if available
        raw_severity = finding.get("severity_reason")
        severity_reason = sanitize_human_text(raw_severity) if raw_severity else None
        if severity_reason:
            issue_html += f"<br><small>{severity_reason}</small>"

        # Add habit tag if habits enabled and configured to show
        if (self.habits_enabled and 
            self.settings.habits_framework.report_integration.show_habit_tags):
            
            habit_info = self._get_habit_info_for_finding(finding, analysis_result)
            
            if habit_info:
                habit_html = self._generate_habit_tag_html(habit_info)
                issue_html += habit_html

        return issue_html

    def _get_habit_info_for_finding(self, finding: dict, analysis_result: dict = None) -> Optional[Dict[str, Any]]:
        """
        Get habit information for a finding with proper context.
        
        Args:
            finding: The compliance finding
            analysis_result: Optional analysis result for context
            
        Returns:
            Habit information dictionary or None
        """
        if self.habits_framework:
            # Use enhanced framework with proper context
            context = {
                "document_type": analysis_result.get("document_type", "Unknown") if analysis_result else "Unknown",
                "discipline": analysis_result.get("discipline", "Unknown") if analysis_result else "Unknown",
                "risk_level": finding.get("risk", "Unknown"),
                "issue_category": finding.get("issue_category", "General")
            }
            return self.habits_framework.map_finding_to_habit(finding, context)
        else:
            # Fallback to legacy function
            try:
                from .habit_mapper import get_habit_for_finding
                legacy_habit = get_habit_for_finding(finding)
                return {
                    "habit_number": 1,  # Default to Habit 1
                    "name": legacy_habit["name"],
                    "explanation": legacy_habit["explanation"],
                    "confidence": 0.5  # Default confidence for legacy
                }
            except ImportError:
                logger.warning("Legacy habit mapper not available")
                return None

    def _generate_habit_tag_html(self, habit_info: Dict[str, Any]) -> str:
        """
        Generate HTML for habit tag based on visibility settings.
        
        Args:
            habit_info: Habit information dictionary
            
        Returns:
            HTML string for habit tag
        """
        habit_number = habit_info.get("habit_number", 1)
        habit_name = sanitize_human_text(habit_info.get("name", "Unknown Habit"))
        explanation = sanitize_human_text(habit_info.get("explanation", ""))
        confidence = habit_info.get("confidence", 0.0)
        
        # Only show if confidence meets threshold
        if confidence < self.settings.habits_framework.advanced.habit_confidence_threshold:
            return ""
        
        # Generate appropriate HTML based on visibility level
        if self.settings.habits_framework.is_prominent():
            # Prominent: Large, detailed badge with confidence indicator
            confidence_indicator = f" ({confidence:.0%} confidence)" if confidence < 0.9 else ""
            habit_html = f'''
            <div class="habit-tag prominent" data-confidence="{confidence:.2f}">
                <div class="habit-badge">
                    🎯 HABIT {habit_number}: {habit_name.upper()}{confidence_indicator}
                </div>
                <div class="habit-quick-tip">
                    {explanation[:120]}{'...' if len(explanation) > 120 else ''}
                </div>
            </div>
            '''
        elif self.settings.habits_framework.is_subtle():
            # Subtle: Small icon with tooltip only
            habit_html = f'''
            <div class="habit-tag subtle" title="Habit {habit_number}: {habit_name} - {explanation}" data-confidence="{confidence:.2f}">
                💡
            </div>
            '''
        else:
            # Moderate: Visible tag with name (default)
            tooltip_text = f"{explanation} (Confidence: {confidence:.0%})"
            habit_html = f'''
            <div class="habit-tag moderate" title="{tooltip_text}" data-confidence="{confidence:.2f}">
                💡 Habit {habit_number}: {habit_name}
            </div>
            '''
        
        return habit_html

    def _generate_recommendation_cell(self, finding: dict) -> str:
        """Generate actionable recommendations cell."""
        recommendation = sanitize_human_text(
            finding.get("personalized_tip")
            or finding.get("suggestion", "Review and update documentation")
        )

        # Add priority indicator if available
        priority = finding.get("priority")
        if priority:
            recommendation = f"<strong>Priority {sanitize_human_text(str(priority))}:</strong> {recommendation}"

        return recommendation

    def _generate_prevention_cell(self, finding: dict, analysis_result: dict = None) -> str:
        """Generate prevention strategies cell using enhanced habit mapper."""
        if not self.habits_enabled:
            # Fallback to basic prevention text
            return '<div class="habit-explanation">Review documentation practices regularly</div>'
        
        # Get habit info with proper context
        habit_info = self._get_habit_info_for_finding(finding, analysis_result)
        if not habit_info:
            return '<div class="habit-explanation">Review documentation practices regularly</div>'
        
        habit_name = sanitize_human_text(habit_info["name"])
        habit_explanation = sanitize_human_text(habit_info["explanation"])
        
        # Build HTML based on visibility level
        html = f'<div class="habit-name">{habit_name}</div>'
        html += f'<div class="habit-explanation">{habit_explanation}</div>'
        
        # Add strategies if moderate or prominent visibility
        if self.settings.habits_framework.is_moderate() or self.settings.habits_framework.is_prominent():
            strategies = habit_info.get("improvement_strategies", [])
            if strategies and self.settings.habits_framework.education.show_improvement_strategies:
                html += '<div class="habit-strategies">'
                html += '<strong>Quick Tips:</strong><ul>'
                for strategy in strategies[:2]:  # Show top 2 strategies
                    html += f'<li>{sanitize_human_text(strategy)}</li>'
                html += '</ul></div>'
        
        return html

    def _generate_confidence_cell(self, finding: dict) -> str:
        """Generate confidence and interactive actions cell."""
        confidence = finding.get("confidence", 0)

        # Confidence indicator
        if isinstance(confidence, (int, float)):
            confidence_html = (
                f'<div class="confidence-indicator">{confidence:.0%} confidence</div>'
            )
        else:
            confidence_html = (
                '<div class="confidence-indicator">Confidence: Unknown</div>'
            )

        # Chat link for clarification
        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        issue_title = sanitize_human_text(finding.get("issue_title", "N/A"))

        chat_context = (
            f"Regarding the finding '{issue_title}' with text '{problematic_text}', "
            f"please provide additional clarification and guidance."
        )
        encoded_chat_context = urllib.parse.quote(chat_context)
        chat_link = (
            f'<a href="chat://{encoded_chat_context}" class="chat-link">Ask AI</a>'
        )

        # Dispute mechanism
        dispute_link = (
            '<a href="dispute://finding" class="chat-link">Dispute Finding</a>'
        )

        return f"{confidence_html}<br>{chat_link}<br>{dispute_link}"

    def _inject_summary_sections(
        self, report_html: str, analysis_result: Dict[str, Any]
    ) -> str:
        narrative = sanitize_human_text(analysis_result.get("narrative_summary", ""))
        if not narrative:
            narrative = "No narrative summary generated."
        report_html = report_html.replace(
            "<!-- Placeholder for narrative summary -->", narrative
        )

        bullet_items = analysis_result.get("bullet_highlights") or []
        if bullet_items:
            bullets_html = "".join(
                f"<li>{sanitize_human_text(item)}</li>" for item in bullet_items
            )
        else:
            bullets_html = "<li>No key highlights available.</li>"
        report_html = report_html.replace(
            "<!-- Placeholder for bullet highlights -->", bullets_html
        )
        return report_html

    def _inject_checklist(
        self, report_html: str, checklist: List[Dict[str, Any]]
    ) -> str:
        if not checklist:
            rows_html = '<tr><td colspan="4">Checklist data was not captured for this analysis.</td></tr>'
        else:
            rows = []
            for item in checklist:
                status = (item.get("status") or "review").lower()
                status_class = (
                    "checklist-status-pass"
                    if status == "pass"
                    else "checklist-status-review"
                )
                status_label = "Pass" if status == "pass" else "Review"
                evidence = (
                    sanitize_human_text(item.get("evidence", ""))
                    or "Not located in document."
                )
                recommendation = sanitize_human_text(item.get("recommendation", ""))
                title = sanitize_human_text(
                    item.get("title", item.get("id", "Checklist item"))
                )
                rows.append(
                    f"<tr><td>{title}</td><td><span class='{status_class}'>{status_label}</span></td><td>{evidence}</td><td>{recommendation}</td></tr>"
                )
            rows_html = "".join(rows)
        return report_html.replace("<!-- Placeholder for checklist rows -->", rows_html)

    def _build_pattern_analysis(self, analysis_result: Dict[str, Any]) -> str:
        findings = analysis_result.get("findings") or []
        if not findings:
            return "<p>No recurring compliance patterns were detected in this document.</p>"
        categories = Counter(
            sanitize_human_text(finding.get("issue_category", "General")) or "General"
            for finding in findings
        )
        top_categories = categories.most_common(3)
        list_items = "".join(
            f"<li>{category}: {count} finding(s)</li>"
            for category, count in top_categories
        )
        return f"<ul>{list_items}</ul>"


    def _generate_personal_development_section(
        self, findings: List[Dict[str, Any]], analysis_result: Dict[str, Any]
    ) -> str:
        """
        Generate the Personal Development Insights section with habit analysis.
        
        This section provides personalized growth recommendations based on
        the 7 Habits framework.
        """
        if not self.habits_framework or not findings:
            return ""
        
        # Map all findings to habits
        habit_findings = []
        for finding in findings:
            context = {
                "document_type": analysis_result.get("document_type", "Unknown"),
                "discipline": analysis_result.get("discipline", "Unknown")
            }
            habit_info = self.habits_framework.map_finding_to_habit(finding, context)
            habit_findings.append({
                "finding": finding,
                "habit": habit_info
            })
        
        # Calculate habit progression metrics
        metrics = self.habits_framework.get_habit_progression_metrics(
            [{"habit_id": hf["habit"]["habit_id"]} for hf in habit_findings]
        )
        
        # Determine if section should be expanded by default
        expanded_class = "expanded" if self.settings.habits_framework.report_integration.habit_section_expanded_by_default else "collapsed"
        expand_icon = "▼" if self.settings.habits_framework.report_integration.habit_section_expanded_by_default else "▶"
        
        # Build HTML
        html = f'''
        <div class="personal-development-section {expanded_class}">
            <h2 class="section-header" onclick="togglePersonalDevelopment()">
                <span class="expand-icon">{expand_icon}</span>
                📈 Personal Development Insights
                <span class="optional-badge">Optional</span>
            </h2>
            
            <div class="section-content">
                <p class="section-intro">
                    Based on your {len(findings)} finding(s), here are personalized growth opportunities 
                    using Stephen Covey's 7 Habits framework:
                </p>
        '''
        
        # Add primary focus area
        if metrics["top_focus_areas"]:
            primary_habit_id, primary_metrics = metrics["top_focus_areas"][0]
            primary_habit = self.habits_framework.get_habit_details(primary_habit_id)
            
            html += f'''
                <div class="primary-focus">
                    <h3>🎯 Primary Focus Area</h3>
                    <div class="focus-card">
                        <div class="habit-title">
                            Habit {primary_habit["number"]}: {primary_habit["name"]}
                        </div>
                        <div class="habit-principle">
                            <em>Principle: {primary_habit["principle"]}</em>
                        </div>
                        <div class="focus-stats">
                            <span class="stat-badge">{primary_metrics["percentage"]}% of findings</span>
                            <span class="stat-badge">{primary_metrics["finding_count"]} findings</span>
                        </div>
                        <div class="habit-description">
                            {primary_habit["description"].strip()}
                        </div>
            '''
            
            # Add improvement strategies if enabled
            if self.settings.habits_framework.education.show_improvement_strategies:
                html += '''
                        <div class="improvement-strategies">
                            <h4>💡 Recommended Actions:</h4>
                            <ul>
                '''
                for strategy in primary_habit["improvement_strategies"][:3]:
                    html += f'<li>{sanitize_human_text(strategy)}</li>'
                html += '''
                            </ul>
                        </div>
                '''
            
            # Add clinical examples if enabled
            if self.settings.habits_framework.education.show_clinical_examples:
                html += '''
                        <div class="clinical-examples">
                            <h4>📋 Clinical Applications:</h4>
                            <ul>
                '''
                for example in primary_habit["clinical_examples"][:2]:
                    html += f'<li>{sanitize_human_text(example)}</li>'
                html += '''
                            </ul>
                        </div>
                '''
            
            html += '''
                    </div>
                </div>
            '''
        
        # Add habit profile chart
        html += '''
            <div class="habit-profile">
                <h3>📊 Your Habit Profile</h3>
                <div class="habit-bars">
        '''
        
        for habit_id in sorted(metrics["habit_breakdown"].keys(), key=lambda x: int(x.split("_")[1])):
            habit_data = metrics["habit_breakdown"][habit_id]
            percentage = habit_data["percentage"]
            mastery = habit_data["mastery_level"]
            
            # Determine bar color based on mastery
            if mastery == "Mastered":
                bar_class = "mastery-mastered"
            elif mastery == "Proficient":
                bar_class = "mastery-proficient"
            elif mastery == "Developing":
                bar_class = "mastery-developing"
            else:
                bar_class = "mastery-needs-focus"
            
            html += f'''
                <div class="habit-bar-row">
                    <div class="habit-label">Habit {habit_data["habit_number"]}</div>
                    <div class="habit-bar-container">
                        <div class="habit-bar {bar_class}" style="width: {min(percentage, 100)}%"></div>
                    </div>
                    <div class="habit-mastery">{mastery}</div>
                </div>
            '''
        
        html += '''
                </div>
                <div class="mastery-legend">
                    <span class="legend-item"><span class="legend-color mastery-mastered"></span> Mastered (&lt;5%)</span>
                    <span class="legend-item"><span class="legend-color mastery-proficient"></span> Proficient (5-15%)</span>
                    <span class="legend-item"><span class="legend-color mastery-developing"></span> Developing (15-25%)</span>
                    <span class="legend-item"><span class="legend-color mastery-needs-focus"></span> Needs Focus (&gt;25%)</span>
                </div>
            </div>
        '''
        
        # Add action items
        html += '''
            <div class="action-items">
                <h3>✅ Next Steps</h3>
                <ol>
                    <li>Review the findings related to your primary focus habit</li>
                    <li>Implement 1-2 recommended strategies this week</li>
                    <li>Track your progress in the dashboard</li>
                    <li>Celebrate improvements and adjust focus as needed</li>
                </ol>
            </div>
        '''
        
        # Add resources link if enabled
        if self.settings.habits_framework.education.show_habit_resources:
            html += '''
            <div class="resources-link">
                <p>
                    <strong>Want to learn more?</strong> 
                    Visit the Growth Journey tab in your dashboard for detailed habit resources, 
                    training modules, and progress tracking.
                </p>
            </div>
            '''
        
        html += '''
            </div>
        </div>
        
        <script>
        function togglePersonalDevelopment() {
            const section = document.querySelector('.personal-development-section');
            const icon = document.querySelector('.personal-development-section .expand-icon');
            
            if (section.classList.contains('collapsed')) {
                section.classList.remove('collapsed');
                section.classList.add('expanded');
                icon.textContent = '▼';
            } else {
                section.classList.remove('expanded');
                section.classList.add('collapsed');
                icon.textContent = '▶';
            }
        }
        </script>
        
        <style>
        .personal-development-section {
            margin: 40px 0;
            border: 2px solid #3498db;
            border-radius: 8px;
            background: #f8f9fa;
        }
        
        .personal-development-section .section-header {
            padding: 15px 20px;
            margin: 0;
            cursor: pointer;
            user-select: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 6px 6px 0 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .personal-development-section .section-header:hover {
            background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
        }
        
        .expand-icon {
            font-size: 14px;
            transition: transform 0.3s;
        }
        
        .optional-badge {
            margin-left: auto;
            background: rgba(255, 255, 255, 0.3);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: normal;
        }
        
        .personal-development-section.collapsed .section-content {
            display: none;
        }
        
        .personal-development-section.expanded .section-content {
            display: block;
        }
        
        .section-content {
            padding: 20px;
        }
        
        .section-intro {
            font-size: 16px;
            color: #555;
            margin-bottom: 20px;
        }
        
        .primary-focus {
            margin: 20px 0;
        }
        
        .focus-card {
            background: white;
            border-left: 5px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .habit-title {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        
        .habit-principle {
            color: #7f8c8d;
            margin-bottom: 12px;
        }
        
        .focus-stats {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stat-badge {
            background: #e8f4f8;
            color: #2980b9;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 14px;
            font-weight: 600;
        }
        
        .habit-description {
            line-height: 1.6;
            color: #34495e;
            margin: 15px 0;
        }
        
        .improvement-strategies, .clinical-examples {
            margin-top: 15px;
        }
        
        .improvement-strategies h4, .clinical-examples h4 {
            color: #2980b9;
            margin-bottom: 10px;
        }
        
        .improvement-strategies ul, .clinical-examples ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .improvement-strategies li, .clinical-examples li {
            margin: 8px 0;
            color: #555;
        }
        
        .habit-profile {
            margin: 30px 0;
        }
        
        .habit-bars {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .habit-bar-row {
            display: flex;
            align-items: center;
            margin: 12px 0;
            gap: 10px;
        }
        
        .habit-label {
            width: 80px;
            font-size: 14px;
            font-weight: 600;
            color: #555;
        }
        
        .habit-bar-container {
            flex: 1;
            height: 24px;
            background: #ecf0f1;
            border-radius: 12px;
            overflow: hidden;
        }
        
        .habit-bar {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 12px;
        }
        
        .mastery-mastered {
            background: linear-gradient(90deg, #27ae60, #2ecc71);
        }
        
        .mastery-proficient {
            background: linear-gradient(90deg, #2980b9, #3498db);
        }
        
        .mastery-developing {
            background: linear-gradient(90deg, #f39c12, #f1c40f);
        }
        
        .mastery-needs-focus {
            background: linear-gradient(90deg, #e74c3c, #c0392b);
        }
        
        .habit-mastery {
            width: 120px;
            font-size: 13px;
            font-weight: 600;
            text-align: right;
        }
        
        .mastery-legend {
            display: flex;
            gap: 15px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #666;
        }
        
        .legend-color {
            width: 20px;
            height: 12px;
            border-radius: 6px;
        }
        
        .action-items {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .action-items h3 {
            color: #856404;
            margin-top: 0;
        }
        
        .action-items ol {
            margin: 10px 0 0 0;
            padding-left: 20px;
        }
        
        .action-items li {
            margin: 8px 0;
            color: #856404;
        }
        
        .resources-link {
            text-align: center;
            padding: 15px;
            background: #e8f4f8;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .resources-link p {
            margin: 0;
            color: #2980b9;
        }
        </style>
        '''
        
        return html
