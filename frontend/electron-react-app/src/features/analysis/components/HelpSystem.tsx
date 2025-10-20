import React, { useState, useRef, useEffect } from "react";
import { Card } from "../../../components/ui/Card";
import { StatusChip } from "../../../components/ui/StatusChip";

import styles from "./HelpSystem.module.css";

interface HelpContent {
  title: string;
  content: string;
  category: "general" | "compliance" | "technical" | "clinical";
}

interface HelpSystemProps {
  className?: string;
}

const HELP_CONTENT: Record<string, HelpContent> = {
  upload_button: {
    title: "Document Upload",
    content:
      "Upload PDF, DOCX, or TXT files for compliance analysis. Scanned documents will be processed with OCR. Supported formats include therapy notes, evaluations, progress reports, and discharge summaries.",
    category: "general",
  },
  rubric_selector: {
    title: "Compliance Rubric",
    content:
      "Select the appropriate compliance rubric for your discipline (PT, OT, SLP) to ensure accurate analysis. The system will auto-detect the most suitable rubric based on document content.",
    category: "compliance",
  },
  analyze_button: {
    title: "Run Analysis",
    content:
      "Start AI-powered compliance analysis. This may take 30-60 seconds depending on document size. The system uses multiple AI models for comprehensive analysis including NER, fact-checking, and compliance scoring.",
    category: "technical",
  },
  compliance_score: {
    title: "Compliance Score",
    content:
      "Overall compliance score from 0-100%. Scores above 85% indicate good compliance. Scores 70-85% suggest minor improvements needed. Scores below 70% require significant documentation improvements.",
    category: "compliance",
  },
  findings_table: {
    title: "Compliance Findings",
    content:
      "Detailed list of compliance issues found in your document, with risk levels and recommendations. Each finding includes specific guidance on how to improve documentation.",
    category: "compliance",
  },
  performance_settings: {
    title: "Performance Settings",
    content:
      "Adjust system performance based on your hardware. Conservative mode for 6-8GB RAM, Aggressive for 12GB+. Higher performance settings enable faster analysis but require more system resources.",
    category: "technical",
  },
  dashboard: {
    title: "Analytics Dashboard",
    content:
      "View historical compliance trends, performance metrics, and insights from your analysis history. Track improvement over time and identify patterns in documentation quality.",
    category: "general",
  },
  chat_assistant: {
    title: "AI Chat Assistant",
    content:
      "Get instant help with compliance questions, documentation best practices, and clinical guidelines. The assistant can explain findings, suggest improvements, and provide educational resources.",
    category: "clinical",
  },
};

const CLINICAL_GUIDES = {
  pt: {
    title: "Physical Therapy Documentation",
    content: `
      <h3>Initial Evaluation Requirements</h3>
      <ul>
        <li><b>History:</b> Relevant medical history, onset of condition, prior therapy</li>
        <li><b>Systems Review:</b> Cardiovascular, musculoskeletal, neuromuscular, integumentary</li>
        <li><b>Tests and Measures:</b> Objective measurements and assessments</li>
        <li><b>Evaluation:</b> Clinical judgment and interpretation of findings</li>
        <li><b>Diagnosis:</b> Physical therapy diagnosis based on examination</li>
        <li><b>Prognosis:</b> Predicted level of improvement and time frame</li>
        <li><b>Plan of Care:</b> Goals, interventions, frequency, and duration</li>
      </ul>

      <h3>Progress Note Requirements</h3>
      <ul>
        <li><b>Subjective:</b> Patient's report of symptoms and functional status</li>
        <li><b>Objective:</b> Measurable findings from examination and treatment</li>
        <li><b>Assessment:</b> Progress toward goals and response to treatment</li>
        <li><b>Plan:</b> Modifications to treatment plan and next steps</li>
      </ul>
    `,
  },
  ot: {
    title: "Occupational Therapy Documentation",
    content: `
      <h3>Evaluation Components</h3>
      <ul>
        <li><b>Occupational Profile:</b> Client's occupational history, interests, values, and needs</li>
        <li><b>Analysis of Occupational Performance:</b> Assessment of client factors, performance skills, and patterns</li>
        <li><b>Activity Demands:</b> Analysis of activities and occupations</li>
        <li><b>Environmental Factors:</b> Physical, social, cultural, and institutional environments</li>
        <li><b>Intervention Plan:</b> Goals, approaches, and methods</li>
      </ul>

      <h3>Documentation Standards</h3>
      <ul>
        <li>Focus on functional outcomes and occupational performance</li>
        <li>Include client-centered goals and interventions</li>
        <li>Document environmental modifications and adaptations</li>
        <li>Assess impact on daily living activities</li>
      </ul>
    `,
  },
  slp: {
    title: "Speech-Language Pathology Documentation",
    content: `
      <h3>Assessment Requirements</h3>
      <ul>
        <li><b>Case History:</b> Medical, developmental, and educational background</li>
        <li><b>Oral Mechanism Examination:</b> Structure and function assessment</li>
        <li><b>Speech-Language Evaluation:</b> Comprehensive testing of communication skills</li>
        <li><b>Swallowing Assessment:</b> If applicable, evaluation of feeding and swallowing</li>
        <li><b>Diagnosis:</b> Speech-language pathology diagnosis</li>
        <li><b>Treatment Plan:</b> Goals, objectives, and intervention strategies</li>
      </ul>

      <h3>Progress Documentation</h3>
      <ul>
        <li>Quantify improvements in communication skills</li>
        <li>Document functional communication abilities</li>
        <li>Include family/caregiver education and training</li>
        <li>Assess impact on academic or vocational performance</li>
      </ul>
    `,
  },
};

export function HelpSystem({ className }: HelpSystemProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("general");
  const [selectedGuide, setSelectedGuide] = useState<string>("pt");
  const [showTooltip, setShowTooltip] = useState<string | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const categories = [
    { key: "general", label: "General Help", icon: "❓" },
    { key: "compliance", label: "Compliance", icon: "📋" },
    { key: "technical", label: "Technical", icon: "⚙️" },
    { key: "clinical", label: "Clinical Guides", icon: "🏥" },
  ];

  const filteredContent = Object.entries(HELP_CONTENT).filter(
    ([_, content]) => content.category === selectedCategory,
  );

  const showTooltipForElement = (helpKey: string) => {
    setShowTooltip(helpKey);
  };

  const hideTooltip = () => {
    setShowTooltip(null);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(event.target as Node)
      ) {
        hideTooltip();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={styles.helpSystem}>
      <Card
        title="📚 Help & Resources"
        subtitle="Comprehensive guidance for therapy compliance documentation"
        className={className}
      >
        <div className={styles.helpContainer}>
          {/* Category Navigation */}
          <div className={styles.categoryNav}>
            {categories.map((category) => (
              <button
                key={category.key}
                className={`${styles.categoryButton} ${selectedCategory === category.key ? styles.active : ""}`}
                onClick={() => setSelectedCategory(category.key)}
              >
                <span className={styles.categoryIcon}>{category.icon}</span>
                <span className={styles.categoryLabel}>{category.label}</span>
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className={styles.contentArea}>
            {selectedCategory === "clinical" ? (
              <div className={styles.clinicalGuides}>
                <div className={styles.guideSelector}>
                  <label className={styles.guideLabel}>
                    Select Discipline:
                  </label>
                  <select
                    value={selectedGuide}
                    onChange={(e) => setSelectedGuide(e.target.value)}
                    className={styles.guideSelect}
                  >
                    <option value="pt">Physical Therapy</option>
                    <option value="ot">Occupational Therapy</option>
                    <option value="slp">Speech-Language Pathology</option>
                  </select>
                </div>

                <div className={styles.guideContent}>
                  <h3 className={styles.guideTitle}>
                    {
                      CLINICAL_GUIDES[
                        selectedGuide as keyof typeof CLINICAL_GUIDES
                      ].title
                    }
                  </h3>
                  <div
                    className={styles.guideText}
                    dangerouslySetInnerHTML={{
                      __html:
                        CLINICAL_GUIDES[
                          selectedGuide as keyof typeof CLINICAL_GUIDES
                        ].content,
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className={styles.helpContent}>
                <h3 className={styles.contentTitle}>
                  {categories.find((c) => c.key === selectedCategory)?.label}{" "}
                  Resources
                </h3>

                <div className={styles.helpItems}>
                  {filteredContent.map(([key, content]) => (
                    <div key={key} className={styles.helpItem}>
                      <div className={styles.helpItemHeader}>
                        <h4 className={styles.helpItemTitle}>
                          {content.title}
                        </h4>
                        <StatusChip
                          label={
                            content.category.charAt(0).toUpperCase() +
                            content.category.slice(1)
                          }
                          status="ready"
                        />
                      </div>
                      <p className={styles.helpItemContent}>
                        {content.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Help Tooltips */}
          <div className={styles.quickHelp}>
            <h4 className={styles.quickHelpTitle}>Quick Help</h4>
            <div className={styles.quickHelpButtons}>
              {Object.entries(HELP_CONTENT)
                .slice(0, 4)
                .map(([key, content]) => (
                  <button
                    key={key}
                    className={styles.quickHelpButton}
                    onClick={() => showTooltipForElement(key)}
                    onMouseEnter={() => showTooltipForElement(key)}
                    onMouseLeave={hideTooltip}
                  >
                    {content.title}
                  </button>
                ))}
            </div>
          </div>
        </div>

        {/* Tooltip */}
        {showTooltip && (
          <div
            ref={tooltipRef}
            className={styles.tooltip}
            style={{
              position: "absolute",
              top: "100%",
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 1000,
            }}
          >
            <div className={styles.tooltipContent}>
              <h4 className={styles.tooltipTitle}>
                {HELP_CONTENT[showTooltip]?.title}
              </h4>
              <p className={styles.tooltipText}>
                {HELP_CONTENT[showTooltip]?.content}
              </p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
