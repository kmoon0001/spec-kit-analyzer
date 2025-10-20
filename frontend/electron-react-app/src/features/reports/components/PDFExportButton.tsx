import React, { useState } from "react";
import {
  Download,
  FileText,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "../../../components/ui/Icons";
import { useAppStore } from "../../../store/useAppStore";
import styles from "./PDFExportButton.module.css";

interface PDFExportOptions {
  includeCharts: boolean;
  includeMetadata: boolean;
  watermark?: string;
  format: "standard" | "detailed" | "summary";
}

interface PDFExportButtonProps {
  analysisId?: string;
  reportData?: any;
  filename?: string;
  variant?: "primary" | "secondary" | "ghost";
  size?: "small" | "medium" | "large";
  disabled?: boolean;
  className?: string;
  onExportStart?: () => void;
  onExportComplete?: (result: any) => void;
  onExportError?: (error: string) => void;
}

export const PDFExportButton: React.FC<PDFExportButtonProps> = ({
  analysisId,
  reportData,
  filename,
  variant = "primary",
  size = "medium",
  disabled = false,
  className = "",
  onExportStart,
  onExportComplete,
  onExportError,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [showOptions, setShowOptions] = useState(false);
  const [options, setOptions] = useState<PDFExportOptions>({
    includeCharts: true,
    includeMetadata: true,
    format: "standard",
  });

  const token = useAppStore((state) => state.auth.token);

  const exportToPDF = async (exportOptions: PDFExportOptions) => {
    if (!token || (!analysisId && !reportData)) {
      onExportError?.("Missing required data for export");
      return;
    }

    setIsExporting(true);
    setExportStatus("idle");
    onExportStart?.();

    try {
      const endpoint = analysisId
        ? `/api/reports/${analysisId}/export/pdf`
        : "/api/reports/export/pdf";

      const payload = analysisId
        ? { ...exportOptions, filename }
        : { report_data: reportData, ...exportOptions, filename };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Export failed: ${response.status}`,
        );
      }

      const result = await response.json();

      if (result.success) {
        // Download the PDF
        if (result.pdf_path) {
          // For file-based export, trigger download
          const downloadResponse = await fetch(
            `/api/reports/download/${result.filename}`,
            {
              headers: { Authorization: `Bearer ${token}` },
            },
          );

          if (downloadResponse.ok) {
            const blob = await downloadResponse.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = result.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
          }
        } else if (result.pdf_data) {
          // For direct PDF data, create blob and download
          const binaryString = atob(result.pdf_data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: "application/pdf" });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = filename || "compliance_report.pdf";
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }

        setExportStatus("success");
        onExportComplete?.(result);

        // Reset status after 3 seconds
        setTimeout(() => setExportStatus("idle"), 3000);
      } else {
        throw new Error(result.error || "Export failed");
      }
    } catch (error) {
      console.error("PDF export error:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Export failed";
      setExportStatus("error");
      onExportError?.(errorMessage);

      // Reset status after 5 seconds
      setTimeout(() => setExportStatus("idle"), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExport = () => {
    if (showOptions) {
      exportToPDF(options);
      setShowOptions(false);
    } else {
      exportToPDF(options);
    }
  };

  const handleOptionsToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowOptions(!showOptions);
  };

  const getButtonIcon = () => {
    if (isExporting) return <Loader2 size={16} className={styles.spinner} />;
    if (exportStatus === "success") return <CheckCircle size={16} />;
    if (exportStatus === "error") return <AlertCircle size={16} />;
    return <Download size={16} />;
  };

  const getButtonText = () => {
    if (isExporting) return "Exporting...";
    if (exportStatus === "success") return "Exported!";
    if (exportStatus === "error") return "Export Failed";
    return "Export PDF";
  };

  const buttonClasses = [
    styles.exportButton,
    styles[variant],
    styles[size],
    exportStatus !== "idle" ? styles[exportStatus] : "",
    isExporting ? styles.loading : "",
    disabled ? styles.disabled : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.container}>
      <div className={styles.buttonGroup}>
        <button
          onClick={handleExport}
          disabled={disabled || isExporting}
          className={buttonClasses}
          title="Export report as PDF"
        >
          {getButtonIcon()}
          <span>{getButtonText()}</span>
        </button>

        <button
          onClick={handleOptionsToggle}
          disabled={disabled || isExporting}
          className={`${styles.optionsButton} ${styles[variant]} ${styles[size]}`}
          title="Export options"
        >
          <FileText size={14} />
        </button>
      </div>

      {showOptions && (
        <div className={styles.optionsPanel}>
          <div className={styles.optionsHeader}>
            <h4>Export Options</h4>
            <button
              onClick={() => setShowOptions(false)}
              className={styles.closeButton}
            >
              ×
            </button>
          </div>

          <div className={styles.optionsContent}>
            <div className={styles.optionGroup}>
              <label className={styles.optionLabel}>
                <input
                  type="checkbox"
                  checked={options.includeCharts}
                  onChange={(e) =>
                    setOptions((prev) => ({
                      ...prev,
                      includeCharts: e.target.checked,
                    }))
                  }
                />
                Include Charts & Visualizations
              </label>
            </div>

            <div className={styles.optionGroup}>
              <label className={styles.optionLabel}>
                <input
                  type="checkbox"
                  checked={options.includeMetadata}
                  onChange={(e) =>
                    setOptions((prev) => ({
                      ...prev,
                      includeMetadata: e.target.checked,
                    }))
                  }
                />
                Include Report Metadata
              </label>
            </div>

            <div className={styles.optionGroup}>
              <label className={styles.selectLabel}>Report Format:</label>
              <select
                value={options.format}
                onChange={(e) =>
                  setOptions((prev) => ({
                    ...prev,
                    format: e.target.value as PDFExportOptions["format"],
                  }))
                }
                className={styles.formatSelect}
              >
                <option value="summary">Summary Report</option>
                <option value="standard">Standard Report</option>
                <option value="detailed">Detailed Report</option>
              </select>
            </div>

            <div className={styles.optionGroup}>
              <label className={styles.selectLabel}>
                Watermark (optional):
              </label>
              <input
                type="text"
                value={options.watermark || ""}
                onChange={(e) =>
                  setOptions((prev) => ({
                    ...prev,
                    watermark: e.target.value || undefined,
                  }))
                }
                placeholder="e.g., CONFIDENTIAL"
                className={styles.watermarkInput}
              />
            </div>

            <div className={styles.optionsActions}>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className={`${styles.exportButton} ${styles.primary} ${styles.small}`}
              >
                {getButtonIcon()}
                Export with Options
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Batch export component for multiple reports
export const BatchPDFExportButton: React.FC<{
  reportIds: string[];
  combined?: boolean;
  onExportComplete?: (results: any) => void;
}> = ({ reportIds, combined = false, onExportComplete }) => {
  const [isExporting, setIsExporting] = useState(false);
  const token = useAppStore((state) => state.auth.token);

  const handleBatchExport = async () => {
    if (!token || reportIds.length === 0) return;

    setIsExporting(true);

    try {
      const response = await fetch("/api/reports/batch-export/pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          report_ids: reportIds,
          combined,
          include_charts: true,
          include_metadata: true,
        }),
      });

      if (!response.ok) {
        throw new Error("Batch export failed");
      }

      const result = await response.json();
      onExportComplete?.(result);

      // Handle download based on result type
      if (result.success) {
        if (combined && result.pdf_data) {
          // Download combined PDF
          const binaryString = atob(result.pdf_data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: "application/pdf" });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "combined_compliance_reports.pdf";
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          // Handle individual files (would need zip download)
          console.log("Individual files exported:", result.results);
        }
      }
    } catch (error) {
      console.error("Batch export error:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      onClick={handleBatchExport}
      disabled={isExporting || reportIds.length === 0}
      className={`${styles.exportButton} ${styles.secondary} ${styles.medium}`}
    >
      {isExporting ? (
        <Loader2 size={16} className={styles.spinner} />
      ) : (
        <Download size={16} />
      )}
      Export {reportIds.length} Reports{" "}
      {combined ? "(Combined)" : "(Individual)"}
    </button>
  );
};
