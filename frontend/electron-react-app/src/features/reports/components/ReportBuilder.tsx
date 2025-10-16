import React, { useState, useCallback } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import {
  Plus,
  Trash2,
  Move,
  Eye,
  Settings,
  BarChart3,
  FileText,
  AlertTriangle,
  CheckCircle,
  Brain,
  Target
} from 'lucide-react';
import styles from './ReportBuilder.module.css';

interface ReportSection {
  id: string;
  type: 'summary' | 'findings' | 'charts' | 'recommendations' | 'metadata' | 'reasoning' | 'custom';
  title: string;
  content?: any;
  settings?: {
    showConfidence?: boolean;
    groupByRisk?: boolean;
    includeEvidence?: boolean;
    chartType?: 'bar' | 'pie' | 'line';
    customContent?: string;
  };
  order: number;
  enabled: boolean;
}

interface ReportBuilderProps {
  analysisData?: any;
  onReportGenerate?: (sections: ReportSection[]) => void;
  onPreview?: (sections: ReportSection[]) => void;
  className?: string;
}

const SECTION_TYPES = [
  { type: 'summary', title: 'Executive Summary', icon: FileText, description: 'High-level compliance overview' },
  { type: 'findings', title: 'Detailed Findings', icon: AlertTriangle, description: 'Compliance issues and violations' },
  { type: 'recommendations', title: 'Recommendations', icon: Target, description: 'Actionable improvement suggestions' },
  { type: 'reasoning', title: 'AI Reasoning', icon: Brain, description: 'Step-by-step analysis process' },
  { type: 'charts', title: 'Charts & Metrics', icon: BarChart3, description: 'Visual compliance data' },
  { type: 'metadata', title: 'Report Metadata', icon: Settings, description: 'Document and analysis details' },
  { type: 'custom', title: 'Custom Section', icon: Plus, description: 'Add your own content' }
] as const;

const DraggableSection: React.FC<{
  section: ReportSection;
  index: number;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  onUpdate: (section: ReportSection) => void;
  onRemove: (id: string) => void;
}> = ({ section, index, onMove, onUpdate, onRemove }) => {
  const [isEditing, setIsEditing] = useState(false);

  const [{ isDragging }, drag] = useDrag({
    type: 'section',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'section',
    hover: (item: { index: number }) => {
      if (item.index !== index) {
        onMove(item.index, index);
        item.index = index;
      }
    },
  });

  const sectionIcon = SECTION_TYPES.find(t => t.type === section.type)?.icon || FileText;
  const IconComponent = sectionIcon;

  const handleSettingsChange = (key: string, value: any) => {
    onUpdate({
      ...section,
      settings: {
        ...section.settings,
        [key]: value
      }
    });
  };

  return (
    <div
      ref={(node) => drag(drop(node))}
      className={`${styles.section} ${isDragging ? styles.dragging : ''} ${!section.enabled ? styles.disabled : ''}`}
    >
      <div className={styles.sectionHeader}>
        <div className={styles.sectionLeft}>
          <Move size={16} className={styles.dragHandle} />
          <IconComponent size={16} className={styles.sectionIcon} />
          <span className={styles.sectionTitle}>{section.title}</span>
        </div>

        <div className={styles.sectionActions}>
          <label className={styles.enableToggle}>
            <input
              type="checkbox"
              checked={section.enabled}
              onChange={(e) => onUpdate({ ...section, enabled: e.target.checked })}
            />
            <span className={styles.toggleSlider} />
          </label>

          <button
            onClick={() => setIsEditing(!isEditing)}
            className={styles.actionButton}
            title="Section settings"
          >
            <Settings size={14} />
          </button>

          <button
            onClick={() => onRemove(section.id)}
            className={`${styles.actionButton} ${styles.danger}`}
            title="Remove section"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {isEditing && (
        <div className={styles.sectionSettings}>
          <div className={styles.settingsGrid}>
            <div className={styles.settingGroup}>
              <label className={styles.settingLabel}>Section Title:</label>
              <input
                type="text"
                value={section.title}
                onChange={(e) => onUpdate({ ...section, title: e.target.value })}
                className={styles.settingInput}
              />
            </div>

            {section.type === 'findings' && (
              <>
                <div className={styles.settingGroup}>
                  <label className={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={section.settings?.showConfidence || false}
                      onChange={(e) => handleSettingsChange('showConfidence', e.target.checked)}
                    />
                    Show AI Confidence Scores
                  </label>
                </div>

                <div className={styles.settingGroup}>
                  <label className={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={section.settings?.groupByRisk || false}
                      onChange={(e) => handleSettingsChange('groupByRisk', e.target.checked)}
                    />
                    Group by Risk Level
                  </label>
                </div>

                <div className={styles.settingGroup}>
                  <label className={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={section.settings?.includeEvidence || false}
                      onChange={(e) => handleSettingsChange('includeEvidence', e.target.checked)}
                    />
                    Include Evidence Citations
                  </label>
                </div>
              </>
            )}

            {section.type === 'charts' && (
              <div className={styles.settingGroup}>
                <label className={styles.settingLabel}>Chart Type:</label>
                <select
                  value={section.settings?.chartType || 'bar'}
                  onChange={(e) => handleSettingsChange('chartType', e.target.value)}
                  className={styles.settingSelect}
                >
                  <option value="bar">Bar Chart</option>
                  <option value="pie">Pie Chart</option>
                  <option value="line">Line Chart</option>
                </select>
              </div>
            )}

            {section.type === 'custom' && (
              <div className={styles.settingGroup}>
                <label className={styles.settingLabel}>Custom Content:</label>
                <textarea
                  value={section.settings?.customContent || ''}
                  onChange={(e) => handleSettingsChange('customContent', e.target.value)}
                  className={styles.settingTextarea}
                  placeholder="Enter custom content for this section..."
                  rows={4}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const ReportBuilder: React.FC<ReportBuilderProps> = ({
  analysisData,
  onReportGenerate,
  onPreview,
  className = ''
}) => {
  const [sections, setSections] = useState<ReportSection[]>([
    {
      id: '1',
      type: 'summary',
      title: 'Executive Summary',
      order: 0,
      enabled: true
    },
    {
      id: '2',
      type: 'findings',
      title: 'Compliance Findings',
      order: 1,
      enabled: true,
      settings: {
        showConfidence: true,
        groupByRisk: true,
        includeEvidence: true
      }
    },
    {
      id: '3',
      type: 'recommendations',
      title: 'Improvement Recommendations',
      order: 2,
      enabled: true
    }
  ]);

  const moveSection = useCallback((dragIndex: number, hoverIndex: number) => {
    setSections(prev => {
      const newSections = [...prev];
      const draggedSection = newSections[dragIndex];
      newSections.splice(dragIndex, 1);
      newSections.splice(hoverIndex, 0, draggedSection);

      // Update order values
      return newSections.map((section, index) => ({
        ...section,
        order: index
      }));
    });
  }, []);

  const addSection = (type: ReportSection['type']) => {
    const sectionType = SECTION_TYPES.find(t => t.type === type);
    if (!sectionType) return;

    const newSection: ReportSection = {
      id: Date.now().toString(),
      type,
      title: sectionType.title,
      order: sections.length,
      enabled: true,
      settings: type === 'custom' ? { customContent: '' } : {}
    };

    setSections(prev => [...prev, newSection]);
  };

  const updateSection = (updatedSection: ReportSection) => {
    setSections(prev => prev.map(section =>
      section.id === updatedSection.id ? updatedSection : section
    ));
  };

  const removeSection = (id: string) => {
    setSections(prev => prev.filter(section => section.id !== id));
  };

  const handlePreview = () => {
    const enabledSections = sections.filter(s => s.enabled).sort((a, b) => a.order - b.order);
    onPreview?.(enabledSections);
  };

  const handleGenerate = () => {
    const enabledSections = sections.filter(s => s.enabled).sort((a, b) => a.order - b.order);
    onReportGenerate?.(enabledSections);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={`${styles.container} ${className}`}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <h3>Report Builder</h3>
            <p>Drag and drop sections to customize your compliance report</p>
          </div>

          <div className={styles.headerActions}>
            <button
              onClick={handlePreview}
              className={`${styles.actionBtn} ${styles.secondary}`}
              disabled={sections.filter(s => s.enabled).length === 0}
            >
              <Eye size={16} />
              Preview
            </button>

            <button
              onClick={handleGenerate}
              className={`${styles.actionBtn} ${styles.primary}`}
              disabled={sections.filter(s => s.enabled).length === 0}
            >
              <CheckCircle size={16} />
              Generate Report
            </button>
          </div>
        </div>

        <div className={styles.content}>
          <div className={styles.sectionsPanel}>
            <h4>Report Sections</h4>
            <div className={styles.sectionsList}>
              {sections.map((section, index) => (
                <DraggableSection
                  key={section.id}
                  section={section}
                  index={index}
                  onMove={moveSection}
                  onUpdate={updateSection}
                  onRemove={removeSection}
                />
              ))}
            </div>
          </div>

          <div className={styles.addPanel}>
            <h4>Add Section</h4>
            <div className={styles.sectionTypes}>
              {SECTION_TYPES.map(({ type, title, icon: Icon, description }) => (
                <button
                  key={type}
                  onClick={() => addSection(type)}
                  className={styles.sectionType}
                  title={description}
                >
                  <Icon size={20} />
                  <span>{title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.footer}>
          <div className={styles.footerStats}>
            <span>{sections.filter(s => s.enabled).length} sections enabled</span>
            <span>•</span>
            <span>{sections.length} total sections</span>
          </div>
        </div>
      </div>
    </DndProvider>
  );
};