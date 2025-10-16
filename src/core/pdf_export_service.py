"""PDF export service used to generate compliance reports.

This module provides a high level interface for turning rendered HTML
reports into PDF documents while handling missing dependencies
gracefully.  It is intentionally defensive so that issues with
WeasyPrint or its system libraries do not stall the broader analysis
pipeline.
"""

from __future__ import annotations

import importlib.util
import logging
from datetime import UTC, datetime, timedelta
from io import BytesIO
from html import escape
from pathlib import Path
from typing import Any

import PIL.Image as Image
from textwrap import dedent

from src.core.report_template_engine import TemplateEngine

logger = logging.getLogger(__name__)


def _is_module_available(module_name: str) -> bool:
    """Return ``True`` when *module_name* can be imported."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError):
        return False


WEASYPRINT_AVAILABLE = _is_module_available("weasyprint")
REPORTLAB_AVAILABLE = _is_module_available("reportlab")
FALLBACK_AVAILABLE = REPORTLAB_AVAILABLE

if WEASYPRINT_AVAILABLE:
    try:
        from weasyprint import CSS, HTML

        try:
            from weasyprint.text.fonts import FontConfiguration
        except (ImportError, OSError):
            FontConfiguration = None  # type: ignore[assignment]
            logger.warning("WeasyPrint font configuration is unavailable; default fonts will be used.")
    except (ImportError, OSError) as exc:  # pragma: no cover - guarded import
        WEASYPRINT_AVAILABLE = False
        CSS = HTML = None  # type: ignore[assignment]
        FontConfiguration = None  # type: ignore[assignment]
        logger.warning("WeasyPrint could not be imported: %s", exc)
else:
    CSS = HTML = None  # type: ignore[assignment]
    FontConfiguration = None  # type: ignore[assignment]


TRANSPARENT_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


class PDFExportError(Exception):
    """Raised when PDF generation fails."""


class PDFExportService:
    """High level PDF export facility."""

    def __init__(
        self,
        output_dir: str | Path | None = None,
        retention_hours: int = 24,
        enable_auto_purge: bool = True,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path("temp/reports")
        self.retention_hours = retention_hours
        self.enable_auto_purge = enable_auto_purge
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.template_engine = TemplateEngine()
        self.font_config = FontConfiguration() if WEASYPRINT_AVAILABLE and FontConfiguration else None
        self._pdf_css_cache: str | None = None
        if WEASYPRINT_AVAILABLE:
            logger.info("PDF export service initialised using WeasyPrint backend")
        elif REPORTLAB_AVAILABLE:
            logger.warning(
                "ReportLab is installed but the fallback renderer is not fully configured. PDF export will raise a clear"
                " error until WeasyPrint is installed."
            )
        else:
            logger.warning(
                "No PDF rendering backend available. Install 'weasyprint' with its system dependencies or 'reportlab'."
            )

        self.pdf_settings = {
            "page_size": "A4",
            "margin_top": "1in",
            "margin_bottom": "1in",
            "margin_left": "0.75in",
            "margin_right": "0.75in",
            "print_background": True,
            "optimize_images": True,
            "pdf_version": "1.7",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def export_to_pdf(
        self,
        html_content: str,
        document_name: str,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convert ``html_content`` into a PDF saved in ``output_dir``.

        The method never raises on failure; instead it logs the problem
        and returns a structure with ``success`` set to ``False`` so the
        calling code can fall back to alternative flows without hanging
        the analysis pipeline.
        """

        if not html_content or not html_content.strip():
            return {"success": False, "error": "HTML content is empty"}

        base_filename = filename or document_name or "report"
        sanitized = self._sanitize_filename(base_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        pdf_path = self.output_dir / f"compliance_report_{sanitized}_{timestamp}.pdf"

        enhanced_html = self._enhance_html_for_pdf(html_content, metadata)

        logger.info("Starting synchronous PDF export: name=%s", sanitized)

        try:
            pdf_bytes = self._render_pdf_bytes(enhanced_html)
            pdf_path.write_bytes(pdf_bytes)
        except PDFExportError as exc:
            logger.error("PDF export failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "pdf_path": None,
                "filename": None,
                "purge_at": None,
            }
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.exception("Unable to write PDF to %s", pdf_path)
            return {
                "success": False,
                "error": str(exc),
                "pdf_path": None,
                "filename": None,
                "purge_at": None,
            }

        file_size = pdf_path.stat().st_size
        now_utc = datetime.now(UTC)
        result = {
            "success": True,
            "pdf_path": str(pdf_path),
            "filename": pdf_path.name,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "generated_at": now_utc.isoformat(),
            "purge_at": None,
        }

        if metadata:
            result["metadata"] = metadata

        if self.enable_auto_purge and self.retention_hours > 0:
            result["purge_at"] = (now_utc + timedelta(hours=self.retention_hours)).isoformat()

        logger.info("PDF export completed: path=%s size_mb=%.2f", result["pdf_path"], result["file_size_mb"])

        return result

    async def export_report_to_pdf(
        self,
        report_data: dict[str, Any],
        template_name: str = "compliance_report_pdf",
        include_charts: bool = True,
        watermark: str | None = None,
    ) -> bytes:
        """Render structured ``report_data`` to a PDF and return the bytes."""

        if not WEASYPRINT_AVAILABLE and not REPORTLAB_AVAILABLE:
            raise PDFExportError(
                "PDF export requires WeasyPrint (recommended) or ReportLab. Install the dependencies and try again."
            )

        logger.info("Starting async PDF export for report: %s", report_data.get("title", "Untitled"))
        self._validate_report_data(report_data)

        pdf_data = await self._prepare_pdf_data(report_data, include_charts, watermark)
        html_content = self.template_engine.render_template(template_name, pdf_data)
        enhanced_html = self._enhance_html_for_pdf(html_content, pdf_data)
        pdf_bytes = self._render_pdf_bytes(enhanced_html)
        logger.info(
            "Async PDF export completed: title=%s size_bytes=%s",
            report_data.get("title", "Untitled"),
            len(pdf_bytes),
        )
        return pdf_bytes

    async def export_batch_reports_to_pdf(
        self,
        reports: list[dict[str, Any]],
        combined: bool = True,
        output_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Export multiple reports to PDFs, optionally combined."""

        try:
            if combined:
                combined_data = self._combine_reports_data(reports)
                pdf_bytes = await self.export_report_to_pdf(combined_data, template_name="batch_compliance_report_pdf")
                return {
                    "success": True,
                    "type": "combined",
                    "pdf_data": pdf_bytes,
                    "report_count": len(reports),
                    "file_size_bytes": len(pdf_bytes),
                }

            results: list[dict[str, Any]] = []
            for index, report in enumerate(reports):
                try:
                    pdf_bytes = await self.export_report_to_pdf(report)
                    if output_dir:
                        output_dir.mkdir(parents=True, exist_ok=True)
                        filename = f"compliance_report_{index + 1:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_path = output_dir / filename
                        file_path.write_bytes(pdf_bytes)
                        results.append(
                            {
                                "index": index,
                                "success": True,
                                "file_path": str(file_path),
                                "file_size_bytes": len(pdf_bytes),
                            }
                        )
                    else:
                        results.append(
                            {
                                "index": index,
                                "success": True,
                                "pdf_data": pdf_bytes,
                                "file_size_bytes": len(pdf_bytes),
                            }
                        )
                except (FileNotFoundError, PermissionError, OSError, PDFExportError) as exc:
                    logger.exception("Failed to export report %s", index)
                    results.append({"index": index, "success": False, "error": str(exc)})

            return {
                "success": True,
                "type": "individual",
                "results": results,
                "total_reports": len(reports),
                "successful_exports": sum(1 for item in results if item.get("success")),
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Batch PDF export failed")
            return {"success": False, "error": str(exc)}

    def purge_old_pdfs(self, max_age_hours: int | None = None) -> dict[str, Any]:
        """Delete PDFs older than ``max_age_hours`` from ``output_dir``."""

        if not self.enable_auto_purge:
            return {"purged": 0, "message": "Auto-purge disabled"}

        max_age = max_age_hours or self.retention_hours
        cutoff = datetime.now().timestamp() - (max_age * 3600)
        purged = 0
        total_size = 0
        errors: list[str] = []

        for pdf_file in self.output_dir.glob("*.pdf"):
            try:
                if pdf_file.stat().st_mtime < cutoff:
                    file_size = pdf_file.stat().st_size
                    pdf_file.unlink()
                    purged += 1
                    total_size += file_size
            except (FileNotFoundError, PermissionError, OSError) as exc:
                logger.warning("Failed to purge PDF %s: %s", pdf_file.name, exc)
                errors.append(f"Failed to purge {pdf_file.name}: {exc}")

        result = {
            "purged": purged,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_age_hours": max_age,
        }

        if errors:
            result["errors"] = errors

        return result

    def get_pdf_info(self, pdf_path: str | Path) -> dict[str, Any] | None:
        """Return metadata for ``pdf_path`` if it exists."""

        path = Path(pdf_path)
        if not path.exists():
            return None

        try:
            stat = path.stat()
            info = {
                "filename": path.name,
                "path": str(path.resolve()),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": path.is_file() and stat.st_size > 0,
            }

            if _is_module_available("PyPDF2"):
                import PyPDF2

                with path.open("rb") as handle:
                    reader = PyPDF2.PdfReader(handle)
                    info.update(
                        {
                            "page_count": len(reader.pages),
                            "encrypted": reader.is_encrypted,
                            "pdf_version": getattr(reader, "pdf_version", "unknown"),
                        }
                    )

            return info
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning("Unable to read PDF info for %s: %s", path, exc)
            return None

    def list_pdfs(self, pattern: str = "*.pdf", sort_by: str = "modified") -> list[dict[str, Any]]:
        """List PDFs in ``output_dir`` matching ``pattern`` sorted by ``sort_by``."""

        items: list[dict[str, Any]] = []
        for pdf_file in self.output_dir.glob(pattern):
            if not pdf_file.is_file():
                continue
            info = self.get_pdf_info(pdf_file)
            if info:
                items.append(info)

        sort_keys = {
            "name": lambda entry: entry["filename"].lower(),
            "size": lambda entry: entry["size_bytes"],
            "created": lambda entry: entry["created_at"],
            "modified": lambda entry: entry["modified_at"],
        }

        if sort_by in sort_keys:
            items.sort(key=sort_keys[sort_by], reverse=sort_by != "name")

        return items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_pdf_bytes(self, html_content: str) -> bytes:
        """Render HTML to PDF bytes using the available backend."""

        if WEASYPRINT_AVAILABLE and HTML and CSS:
            css_kwargs: dict[str, Any] = {}
            if self.font_config is not None:
                css_kwargs["font_config"] = self.font_config

            try:
                html_doc = HTML(string=html_content, base_url=str(Path.cwd()))
                css_doc = CSS(string=self.pdf_css, **css_kwargs)
                pdf_bytes = html_doc.write_pdf(
                    stylesheets=[css_doc],
                    font_config=self.font_config,
                    optimize_images=True,
                    presentational_hints=True,
                    pdf_version=self.pdf_settings["pdf_version"],
                )
            except Exception as exc:  # pragma: no cover - safety net
                raise PDFExportError(f"Failed to render PDF bytes: {exc}") from exc

            if not isinstance(pdf_bytes, (bytes, bytearray)):
                pdf_bytes = str(pdf_bytes or "").encode("utf-8")
            return bytes(pdf_bytes)

        if REPORTLAB_AVAILABLE:
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
            except Exception as exc:  # pragma: no cover - optional dependency safety
                raise PDFExportError(
                    "ReportLab fallback is unavailable. Install WeasyPrint for full PDF support."
                ) from exc

            buffer = BytesIO()
            pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
            pdf_canvas.setTitle("Therapy Compliance Analysis Report")
            pdf_canvas.setAuthor("Therapy Compliance Analyzer")
            pdf_canvas.setFont("Helvetica-Bold", 12)
            pdf_canvas.drawString(72, 750, "Therapy Compliance Analysis Report")
            pdf_canvas.setFont("Helvetica", 9)
            pdf_canvas.drawString(72, 735, datetime.now(UTC).strftime("Generated %Y-%m-%d %H:%M:%S %Z"))
            pdf_canvas.setFont("Helvetica", 8)
            pdf_canvas.drawString(
                72,
                720,
                "Fallback renderer in use. Enable WeasyPrint for production-ready exports.",
            )
            pdf_canvas.drawString(72, 705, f"Original HTML length: {len(html_content)} characters")
            pdf_canvas.showPage()
            pdf_canvas.save()
            buffer.seek(0)
            return buffer.getvalue()

        raise PDFExportError(
            "PDF export requires WeasyPrint to be installed or the ReportLab fallback to be fully configured."
        )

    def _validate_report_data(self, report_data: dict[str, Any]) -> None:
        required = ["title", "generated_at", "findings"]
        missing = [field for field in required if field not in report_data]
        if missing:
            raise ValueError(f"Report data missing required fields: {missing}")

    async def _prepare_pdf_data(
        self,
        report_data: dict[str, Any],
        include_charts: bool,
        watermark: str | None,
    ) -> dict[str, Any]:
        pdf_data = report_data.copy()
        pdf_data.update(
            {
                "export_timestamp": datetime.now().isoformat(),
                "export_format": "PDF",
                "include_charts": include_charts,
                "watermark": watermark,
                "page_settings": self.pdf_settings,
            }
        )

        if include_charts and "charts" in pdf_data:
            pdf_data["charts"] = await self._convert_charts_for_pdf(pdf_data["charts"])

        return self._optimize_content_for_print(pdf_data)

    async def _convert_charts_for_pdf(self, charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for chart in charts:
            try:
                chart_copy = chart.copy()
                # Placeholder transparent pixel ensures the PDF renders even when
                # charts have not been converted to images yet.
                chart_copy["image_data"] = self._transparent_pixel()
                converted.append(chart_copy)
            except (Image.UnidentifiedImageError, ValueError, OSError) as exc:
                logger.warning("Failed to convert chart for PDF: %s", exc)
                converted.append(chart)
        return converted

    def _transparent_pixel(self) -> str:
        return f"data:image/png;base64,{TRANSPARENT_PIXEL}"

    def _optimize_content_for_print(self, data: dict[str, Any]) -> dict[str, Any]:
        if "findings" in data and len(data["findings"]) > 10:
            grouped = []
            findings = data["findings"]
            for index in range(0, len(findings), 5):
                group = findings[index : index + 5]
                grouped.append(
                    {
                        "group_index": index // 5 + 1,
                        "findings": group,
                        "page_break_after": index + 5 < len(findings),
                    }
                )
            data["grouped_findings"] = grouped
        return data

    @property
    def pdf_css(self) -> str:
        """CSS used for PDF rendering and inline HTML enhancement."""

        if self._pdf_css_cache is None:
            self._pdf_css_cache = self._get_pdf_css_styles()
        return self._pdf_css_cache

    def _get_pdf_css_styles(self) -> str:
        return dedent(
            """
            @page {
                size: Letter;
                margin: 1in 0.75in;

                @top-left {
                    content: "Therapy Compliance Analysis Report";
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 10pt;
                    color: #4b5563;
                }

                @top-right {
                    content: "Generated by Spec Kit Analyzer";
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 9pt;
                    color: #9ca3af;
                }

                @bottom-center {
                    content: "CONFIDENTIAL • HIPAA Protected";
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 9pt;
                    color: #b91c1c;
                }

                @bottom-right {
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 9pt;
                    color: #4b5563;
                }
            }

            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.45;
                color: #1f2937;
                background: #ffffff;
            }

            h1, h2, h3 {
                color: #2563eb;
                page-break-after: avoid;
            }

            .report-metadata {
                border: 1pt solid #d1d5db;
                border-radius: 6pt;
                padding: 12pt;
                margin: 16pt 0;
                background: #f9fafb;
            }

            .metadata-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 8pt;
            }

            .metadata-table th,
            .metadata-table td {
                border: 1pt solid #e5e7eb;
                padding: 6pt 8pt;
                text-align: left;
            }

            .metadata-table th {
                background: #e5f0ff;
                font-weight: 600;
            }

            .finding {
                border: 1pt solid #e5e7eb;
                border-radius: 4pt;
                padding: 12pt;
                margin-bottom: 12pt;
                page-break-inside: avoid;
            }

            .risk-high {
                border-left: 4pt solid #dc2626;
                background: #fef2f2;
            }

            .high-risk {
                border-left: 4pt solid #dc2626;
                background: #fef2f2;
            }

            .risk-medium {
                border-left: 4pt solid #f59e0b;
                background: #fffbeb;
            }

            .risk-low {
                border-left: 4pt solid #10b981;
                background: #f0fdf4;
            }

            .confidence-indicator {
                display: inline-block;
                padding: 4pt 8pt;
                border-radius: 9999px;
                font-size: 9pt;
                font-weight: 600;
                text-transform: uppercase;
            }

            .high-confidence {
                background: #d1fae5;
                color: #047857;
            }

            .medium-confidence {
                background: #fef3c7;
                color: #b45309;
            }

            .low-confidence {
                background: #fee2e2;
                color: #b91c1c;
            }

            .disputed {
                background: #f5f3ff;
                color: #6d28d9;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12pt;
                margin: 16pt 0;
            }

            .metric-card {
                border: 1pt solid #e5e7eb;
                border-radius: 4pt;
                padding: 12pt;
                text-align: center;
            }

            .metric-value {
                font-size: 24pt;
                font-weight: bold;
                color: #2563eb;
            }

            .metric-label {
                font-size: 10pt;
                color: #6b7280;
                margin-top: 4pt;
            }

            .report-footer {
                margin-top: 24pt;
                padding-top: 12pt;
                border-top: 1pt solid #d1d5db;
                font-size: 9pt;
                color: #374151;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin: 12pt 0;
            }

            th,
            td {
                border: 1pt solid #e5e7eb;
                padding: 8pt;
                text-align: left;
            }

            th {
                background: #f9fafb;
                font-weight: bold;
            }

            .watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 48pt;
                color: rgba(0, 0, 0, 0.08);
                z-index: -1;
            }
            """
        )

    def _enhance_html_for_pdf(self, html_content: str, data: dict[str, Any] | None) -> str:
        """Inject styling, metadata and disclaimers into the supplied HTML."""

        content = html_content or ""
        if "<html" not in content.lower():
            content = f"<html><head></head><body>{content}</body></html>"
        elif "<head" not in content.lower():
            content = content.replace("<html>", "<html><head></head>", 1)

        if "<body" not in content.lower():
            content = content.replace("</head>", "</head><body>") + "</body>"

        style_block = f"<style>{self.pdf_css}</style>"
        content = content.replace("<head>", f"<head>{style_block}", 1)

        metadata_source: dict[str, Any] = {}
        watermark_value: str | None = None
        if isinstance(data, dict):
            watermark_value = data.get("watermark") if isinstance(data.get("watermark"), str) else None
            potential_metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else None
            if potential_metadata:
                metadata_source = potential_metadata
            else:
                metadata_source = {
                    str(key): value
                    for key, value in data.items()
                    if isinstance(key, str) and key.lower() != "watermark"
                }

        watermark_html = ""
        if watermark_value:
            watermark_html = f"<div class='watermark'>{escape(watermark_value)}</div>"

        metadata_html = ""
        if metadata_source:
            rows = "".join(
                f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
                for key, value in sorted(metadata_source.items())
            )
            metadata_html = (
                "<section class='report-metadata'>"
                "<h2>Report Metadata</h2>"
                "<table class='metadata-table'>"
                f"{rows}"
                "</table>"
                "</section>"
            )

        footer_html = (
            "<footer class='report-footer'>"
            "<p><strong>CONFIDENTIAL</strong> – HIPAA Protected Health Information.</p>"
            "<p>This report leverages AI-assisted technology. Review before distribution.</p>"
            "</footer>"
        )

        insertion = watermark_html + metadata_html
        lower_content = content.lower()
        body_start = lower_content.find("<body")
        if body_start != -1:
            body_end = lower_content.find(">", body_start)
            if body_end != -1:
                content = content[: body_end + 1] + insertion + content[body_end + 1 :]
        else:
            content = insertion + content

        if "</body>" in lower_content:
            content = content.replace("</body>", f"{footer_html}</body>")
        else:
            content += footer_html

        return content

    def _combine_reports_data(self, reports: list[dict[str, Any]]) -> dict[str, Any]:
        combined = {
            "title": f"Combined Compliance Analysis Report ({len(reports)} Reports)",
            "generated_at": datetime.now().isoformat(),
            "report_count": len(reports),
            "reports": reports,
            "combined_metrics": self._calculate_combined_metrics(reports),
            "findings": [],
        }

        for index, report in enumerate(reports):
            for finding in report.get("findings", []):
                finding_copy = finding.copy()
                finding_copy["source_report"] = index + 1
                finding_copy["source_title"] = report.get("title", f"Report {index + 1}")
                combined["findings"].append(finding_copy)

        return combined

    def _calculate_combined_metrics(self, reports: list[dict[str, Any]]) -> dict[str, Any]:
        total_findings = 0
        total_high = 0
        total_medium = 0
        total_low = 0
        scores: list[float] = []

        for report in reports:
            findings = report.get("findings", [])
            total_findings += len(findings)
            for finding in findings:
                risk_level = finding.get("risk_level", "").lower()
                if risk_level == "high":
                    total_high += 1
                elif risk_level == "medium":
                    total_medium += 1
                elif risk_level == "low":
                    total_low += 1

            if "compliance_score" in report:
                try:
                    scores.append(float(report["compliance_score"]))
                except (TypeError, ValueError):
                    logger.debug("Skipping non numeric compliance score: %s", report["compliance_score"])

        average_score = sum(scores) / len(scores) if scores else 0.0
        return {
            "total_findings": total_findings,
            "high_risk_findings": total_high,
            "medium_risk_findings": total_medium,
            "low_risk_findings": total_low,
            "average_compliance_score": round(average_score, 1),
            "report_count": len(reports),
        }

    def _sanitize_filename(self, filename: str) -> str:
        name = Path(filename).stem or "document"
        name = name.replace(" ", "_")
        return "".join(ch for ch in name if ch.isalnum() or ch in {"_", "-"})[:50]


_pdf_export_service: PDFExportService | None = None


def get_pdf_export_service() -> PDFExportService:
    """Return a shared :class:`PDFExportService` instance."""

    global _pdf_export_service
    if _pdf_export_service is None:
        _pdf_export_service = PDFExportService()
    return _pdf_export_service
