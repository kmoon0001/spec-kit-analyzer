import React, { useState, useRef } from 'react';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';
import { StatusChip } from '../../../components/ui/StatusChip';
import { ChatAssistant } from './ChatAssistant';

import styles from './ReportDialog.module.css';

interface ReportDialogProps {
    reportHtml: string;
    reportData?: {
        complianceScore: number;
        findings: any[];
        documentName: string;
        analysisDate: string;
        discipline: string;
        rubric: string;
    };
    onClose?: () => void;
    className?: string;
}

export function ReportDialog({ reportHtml, reportData, onClose, className }: ReportDialogProps) {
    const [activeTab, setActiveTab] = useState<'report' | 'chat'>('report');
    const [isExporting, setIsExporting] = useState(false);
    const reportRef = useRef<HTMLDivElement>(null);

    const handlePrintToPDF = async () => {
        setIsExporting(true);

        try {
            // Create a new window for printing
            const printWindow = window.open('', '_blank');
            if (!printWindow) {
                throw new Error('Unable to open print window');
            }

            // Write the HTML content to the new window
            printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Compliance Analysis Report</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              margin: 0;
              padding: 20px;
              color: #333;
              line-height: 1.6;
            }
            .report-header {
              text-align: center;
              margin-bottom: 30px;
              padding-bottom: 20px;
              border-bottom: 2px solid #3b82f6;
            }
            .report-title {
              font-size: 24px;
              font-weight: 700;
              color: #1f2937;
              margin-bottom: 8px;
            }
            .report-subtitle {
              color: #6b7280;
              font-size: 16px;
            }
            .report-meta {
              display: flex;
              justify-content: space-between;
              margin: 20px 0;
              padding: 15px;
              background: #f8fafc;
              border-radius: 8px;
            }
            .meta-item {
              text-align: center;
            }
            .meta-label {
              font-size: 12px;
              color: #6b7280;
              text-transform: uppercase;
              letter-spacing: 0.5px;
            }
            .meta-value {
              font-size: 18px;
              font-weight: 600;
              color: #1f2937;
              margin-top: 4px;
            }
            .compliance-score {
              color: #059669;
            }
            .findings-section {
              margin: 30px 0;
            }
            .findings-title {
              font-size: 20px;
              font-weight: 600;
              color: #1f2937;
              margin-bottom: 16px;
            }
            .finding-item {
              margin: 16px 0;
              padding: 16px;
              border-left: 4px solid #3b82f6;
              background: #f8fafc;
              border-radius: 0 8px 8px 0;
            }
            .finding-severity {
              display: inline-block;
              padding: 4px 8px;
              border-radius: 4px;
              font-size: 12px;
              font-weight: 600;
              text-transform: uppercase;
              margin-bottom: 8px;
            }
            .severity-high {
              background: #fee2e2;
              color: #991b1b;
            }
            .severity-medium {
              background: #fef3c7;
              color: #92400e;
            }
            .severity-low {
              background: #d1fae5;
              color: #065f46;
            }
            .finding-description {
              color: #4b5563;
              line-height: 1.5;
            }
            .recommendations {
              margin: 30px 0;
              padding: 20px;
              background: #eff6ff;
              border-radius: 8px;
            }
            .recommendations-title {
              font-size: 18px;
              font-weight: 600;
              color: #1e40af;
              margin-bottom: 12px;
            }
            .recommendations-list {
              color: #1e40af;
            }
            .recommendations-list li {
              margin: 8px 0;
            }
            @media print {
              body { margin: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="report-header">
            <div class="report-title">Therapy Compliance Analysis Report</div>
            <div class="report-subtitle">AI-Powered Documentation Review</div>
          </div>

          ${reportData ? `
            <div class="report-meta">
              <div class="meta-item">
                <div class="meta-label">Document</div>
                <div class="meta-value">${reportData.documentName}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Discipline</div>
                <div class="meta-value">${reportData.discipline.toUpperCase()}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Compliance Score</div>
                <div class="meta-value compliance-score">${reportData.complianceScore.toFixed(1)}%</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Analysis Date</div>
                <div class="meta-value">${new Date(reportData.analysisDate).toLocaleDateString()}</div>
              </div>
            </div>
          ` : ''}

          <div class="findings-section">
            <div class="findings-title">Compliance Findings</div>
            ${reportData?.findings?.map((finding: any, index: number) => `
              <div class="finding-item">
                <div class="finding-severity severity-${(finding.severity || 'low').toLowerCase()}">
                  ${(finding.severity || 'Low').toUpperCase()}
                </div>
                <div class="finding-description">
                  ${finding.description || finding.summary || 'See detailed report for more information.'}
                </div>
              </div>
            `).join('') || '<p>No specific findings to report.</p>'}
          </div>

          <div class="recommendations">
            <div class="recommendations-title">Recommendations</div>
            <ul class="recommendations-list">
              <li>Review and address all high-severity findings</li>
              <li>Ensure all goals are specific, measurable, and time-bound</li>
              <li>Document functional outcomes and patient progress clearly</li>
              <li>Include medical necessity justification for continued treatment</li>
              <li>Verify all documentation meets Medicare requirements</li>
            </ul>
          </div>

          <div style="margin-top: 40px; text-align: center; color: #6b7280; font-size: 12px;">
            Generated by Therapy Compliance Analyzer • ${new Date().toLocaleString()}
          </div>
        </body>
        </html>
      `);

            printWindow.document.close();

            // Wait for content to load, then trigger print
            setTimeout(() => {
                printWindow.print();
                printWindow.close();
            }, 500);

        } catch (error) {
            console.error('Error printing to PDF:', error);
            alert('Unable to print report. Please try again.');
        } finally {
            setIsExporting(false);
        }
    };

    const handleExportHTML = () => {
        const blob = new Blob([reportHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const tabs = [
        { key: 'report', label: '📄 Report', icon: '📄' },
        { key: 'chat', label: '💬 Chat Assistant', icon: '💬' }
    ];

    return (
        <div className={styles.reportDialog}>
            <Card title="📊 Analysis Report" subtitle="Detailed compliance analysis with interactive features" className={className}>
                <div className={styles.reportContainer}>
                    {/* Tab Navigation */}
                    <div className={styles.tabNav}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                className={`${styles.tabButton} ${activeTab === tab.key ? styles.active : ''}`}
                                onClick={() => setActiveTab(tab.key as 'report' | 'chat')}
                            >
                                <span className={styles.tabIcon}>{tab.icon}</span>
                                <span className={styles.tabLabel}>{tab.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Content Area */}
                    <div className={styles.contentArea}>
                        {activeTab === 'report' ? (
                            <div className={styles.reportContent}>
                                {/* Report Actions */}
                                <div className={styles.reportActions}>
                                    <div className={styles.actionButtons}>
                                        <Button
                                            onClick={handlePrintToPDF}
                                            disabled={isExporting}
                                            className={styles.exportButton}
                                        >
                                            {isExporting ? '🔄 Exporting...' : '📄 Export PDF'}
                                        </Button>
                                        <Button
                                            variant="outline"
                                            onClick={handleExportHTML}
                                            className={styles.exportButton}
                                        >
                                            💾 Export HTML
                                        </Button>
                                    </div>

                                    {reportData && (
                                        <div className={styles.reportSummary}>
                                            <StatusChip
                                                label={`${reportData.complianceScore.toFixed(1)}% Compliant`}
                                                status={reportData.complianceScore > 85 ? 'ready' :
                                                    reportData.complianceScore > 70 ? 'warming' : 'warning'}
                                            />
                                            <span className={styles.reportMeta}>
                                                {reportData.findings?.length || 0} findings • {reportData.discipline.toUpperCase()}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Report Content */}
                                <div
                                    ref={reportRef}
                                    className={styles.reportDisplay}
                                    dangerouslySetInnerHTML={{ __html: reportHtml }}
                                />
                            </div>
                        ) : (
                            <div className={styles.chatContent}>
                                <ChatAssistant
                                    initialContext={reportData ?
                                        `I just analyzed a ${reportData.discipline.toUpperCase()} document with a compliance score of ${reportData.complianceScore.toFixed(1)}%. Can you help me understand the findings and suggest improvements?`
                                        : "I need help understanding compliance findings and improving documentation."
                                    }
                                />
                            </div>
                        )}
                    </div>

                    {/* Footer Actions */}
                    <div className={styles.footerActions}>
                        <div className={styles.footerInfo}>
                            <span className={styles.generatedTime}>
                                Generated {new Date().toLocaleString()}
                            </span>
                            <StatusChip label="AI-Powered Analysis" status="ready" />
                        </div>

                        <div className={styles.footerButtons}>
                            <Button variant="ghost" onClick={onClose}>
                                Close
                            </Button>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}
