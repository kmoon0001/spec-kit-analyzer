# Standard library
import os
import json
import logging
import math
import textwrap
from typing import Optional, Tuple
from datetime import datetime

# Third-party
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMessageBox
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Local imports
from .database import get_str_setting, get_bool_setting, _get_db_connection, set_setting, get_setting
from .utils import _now_iso

logger = logging.getLogger(__name__)

# PDF report defaults
REPORT_FONT_FAMILY = "DejaVu Sans"
REPORT_FONT_SIZE = 8.5
REPORT_PAGE_SIZE = (8.27, 11.69)  # A4 inches
REPORT_MARGINS = (1.1, 1.0, 1.3, 1.0)  # top, right, bottom, left inches
REPORT_HEADER_LINES = 2
REPORT_FOOTER_LINES = 1
REPORT_TEMPLATE_VERSION = "v2.0"

def _format_mmddyyyy(dt) -> str:
    return dt.strftime("%m%d%Y")

def _next_report_number() -> int:
    today = _format_mmddyyyy(datetime.now())
    last_date = get_setting("last_report_date")
    raw = get_setting("report_counter")
    if last_date != today or raw is None:
        num = 1
    else:
        try:
            num = int(raw)
        except (ValueError, TypeError):
            num = 1
    set_setting("report_counter", str(num + 1))
    set_setting("last_report_date", today)
    return num

def generate_report_paths() -> Tuple[str, str]:
    from .database import ensure_reports_dir_configured
    base = ensure_reports_dir_configured()
    stem = f"{_format_mmddyyyy(datetime.now())}report{_next_report_number()}"
    return os.path.join(base, f"{stem}.pdf"), os.path.join(base, f"{stem}.csv")

def export_report_json(obj: dict, json_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to export JSON: {e}")
        return False


def export_report_pdf(lines: list[str], pdf_path: str, meta: Optional[dict] = None,
                      chart_data: Optional[dict] = None,
                      sev_counts: Optional[dict] = None,
                      cat_counts: Optional[dict] = None) -> bool:
    try:
        if not QApplication.instance():
            import matplotlib
            matplotlib.use("Agg")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        theme = (get_str_setting("pdf_chart_theme", "dark") or "dark").lower()
        if theme == "light":
            chart_colors = ["#b91c1c", "#b45309", "#047857", "#374151"]
            xtick = ytick = "#111827"; spine = "#6b7280"; fig_face = ax_face = "#ffffff"; ylabel_color = "#111827"
        else:
            chart_colors = ["#ef4444", "#f59e0b", "#10b981", "#9ca3af"]
            xtick = ytick = "#e5e7eb"; spine = "#9aa1a8"; fig_face = ax_face = "#2b2b2b"; ylabel_color = "#e5e7eb"

        font_family = REPORT_FONT_FAMILY
        font_size = REPORT_FONT_SIZE
        page_w, page_h = REPORT_PAGE_SIZE
        margin_top, margin_right, margin_bottom, margin_left = REPORT_MARGINS
        usable_width_in = page_w - (margin_left + margin_right)
        approx_char_width_in = max(0.12, (font_size * 0.56) / 72.0)
        chars_per_line = max(56, int(usable_width_in / approx_char_width_in))

        wrapped: list[str] = []
        for ln in lines:
            s = "" if ln is None else str(ln).replace("<b>", "*").replace("</b>", "*")
            if not s:
                wrapped.append("")
                continue
            for block in textwrap.wrap(s, width=chars_per_line, replace_whitespace=False, drop_whitespace=False):
                wrapped.append(block)
            if s.endswith(":") or s.istitle(): wrapped.append("")

        line_height_in = (font_size / 72.0) * 2.0
        usable_height_in = page_h - (margin_top + margin_bottom)
        header_lines = REPORT_HEADER_LINES; footer_lines = REPORT_FOOTER_LINES

        chart_enabled = get_bool_setting("pdf_chart_enabled", True)
        chart_position = (get_str_setting("pdf_chart_position", "bottom") or "bottom").lower()
        if not chart_enabled or chart_position == "none":
            chart_data = sev_counts = cat_counts = None

        top_chart_h = 0.12; bottom_charts_h = 0.26
        chart_on_top = (chart_data is not None) and (chart_position == "top")
        chart_on_bottom = (chart_data is not None) and (chart_position == "bottom")

        reserved_top = top_chart_h if chart_on_top else 0.0
        reserved_bottom = bottom_charts_h if chart_on_bottom else 0.0
        header_reserve_in = header_lines * line_height_in
        footer_reserve_in = footer_lines * line_height_in
        text_area_height_in = usable_height_in * (1.0 - reserved_top - reserved_bottom) - header_reserve_in - footer_reserve_in
        if text_area_height_in < (12 * line_height_in):
            chart_on_top = chart_on_bottom = False
            reserved_top = reserved_bottom = 0.0
            text_area_height_in = usable_height_in - header_reserve_in - footer_reserve_in
        lines_per_page = max(10, int(text_area_height_in / line_height_in))

        risk_label = (meta or {}).get("risk_label", "")
        risk_color = (meta or {}).get("risk_color", "#6b7280")
        header_left = meta.get("file_name", "") if meta else ""
        header_right = f"{meta.get('run_time', _now_iso())} | Template {REPORT_TEMPLATE_VERSION}" if meta else _now_iso()

        with PdfPages(pdf_path) as pdf:
            total_lines = len(wrapped)
            total_pages = max(1, math.ceil(total_lines / lines_per_page))
            for page_idx in range(total_pages):
                start = page_idx * lines_per_page
                end = min(start + lines_per_page, total_lines)
                page_lines = wrapped[start:end]

                fig = plt.figure(figsize=(page_w, page_h))
                fig.patch.set_facecolor(fig_face)
                ax = fig.add_axes([
                    margin_left / page_w, margin_bottom / page_h,
                    (page_w - margin_left - margin_right) / page_w,
                    (page_h - margin_top - margin_bottom) / page_h,
                ])
                ax.set_facecolor(ax_face); ax.axis("off")

                ax.text(0, 1, header_left, va="top", ha="left", family=font_family, fontsize=font_size + 1.0, color=xtick)
                ax.text(1, 1, header_right, va="top", ha="right", family=font_family, fontsize=font_size + 1.0, color=xtick)

                try:
                    if risk_label:
                        ax.add_patch(FancyBboxPatch(
                            (0.82, 0.965), 0.16, 0.05, boxstyle="round,pad=0.008,rounding_size=0.01",
                            linewidth=0.0, facecolor=risk_color, transform=ax.transAxes
                        ))
                        ax.text(0.90, 0.99, f"Risk: {risk_label}", va="top", ha="center",
                                family=font_family, fontsize=font_size + 0.6,
                                color="#111827" if risk_label != "High" else "#ffffff",
                                transform=ax.transAxes)
                except Exception: ...

                if page_idx == 0 and chart_on_top:
                    try:
                        cats = ["Flags", "Wobblers", "Suggestions", "Notes"]
                        vals = [sev_counts.get("flag", 0), sev_counts.get("wobbler", 0),
                                sev_counts.get("suggestion", 0), sev_counts.get("auditor_note", 0)] if sev_counts else [0, 0, 0, 0]
                        ax_chart = fig.add_axes([0.07, 0.81, 0.86, 0.12])
                        ax_chart.bar(cats, vals, color=chart_colors)
                        ax_chart.set_ylabel("Count", fontsize=font_size + 0.6, color=ylabel_color)
                        ax_chart.set_facecolor(ax_face)
                        for lab in ax_chart.get_xticklabels(): lab.set_fontsize(font_size + 0.3); lab.set_color(xtick)
                        for lab in ax_chart.get_yticklabels(): lab.set_fontsize(font_size - 0.1); lab.set_color(ytick)
                        for sp in ax_chart.spines.values(): sp.set_color(spine)
                    except Exception: ...

                ax.text(0.5, 0, f"Page {page_idx + 1} / {total_pages}", va="bottom", ha="center", family=font_family, fontsize=font_size, color=xtick)

                y_text_top = 1 - ((REPORT_HEADER_LINES * line_height_in) / (page_h - (margin_top + margin_bottom)))
                if page_idx == 0 and chart_on_top: y_text_top -= (top_chart_h + 0.02)

                cursor_y = y_text_top
                y_step = line_height_in / (page_h - (margin_top + margin_bottom))
                for ln in page_lines:
                    is_section_header = bool(ln and ln.startswith("---") and ln.endswith("---"))
                    if is_section_header:
                        cursor_y -= y_step * 0.5
                        ax.axhline(y=cursor_y + (y_step * 0.2), xmin=0, xmax=1, color=spine, linewidth=0.7)
                        cursor_y -= y_step * 0.2
                        ax.text(0.5, cursor_y, ln.strip("- "), va="top", ha="center", family=font_family,
                                fontsize=font_size + 1.5, color=xtick, weight="bold")
                        cursor_y -= y_step * 1.2
                        ax.axhline(y=cursor_y + (y_step * 0.5), xmin=0, xmax=1, color=spine, linewidth=0.7)
                        cursor_y -= y_step * 0.5
                    else:
                        is_finding_header = bool(ln and ln.startswith("["))
                        weight = "bold" if is_finding_header else "normal"
                        size = font_size + (0.5 if is_finding_header else 0)
                        ax.text(0, cursor_y, ln, va="top", ha="left", family=font_family, fontsize=size, color=xtick, weight=weight)
                    cursor_y -= y_step

                if (page_idx == total_pages - 1) and chart_on_bottom and (sev_counts or cat_counts):
                    try:
                        y0 = 0.08; h = 0.16
                        if sev_counts:
                            cats = ["Flags", "Wobblers", "Suggestions", "Notes"]
                            vals = [sev_counts.get("flag", 0), sev_counts.get("wobbler", 0),
                                    sev_counts.get("suggestion", 0), sev_counts.get("auditor_note", 0)]
                            ax_s = fig.add_axes([0.07, y0, 0.40, h])
                            ax_s.bar(cats, vals, color=["#ef4444", "#f59e0b", "#10b981", "#9ca3af"])
                            ax_s.set_title("Findings by Severity", fontsize=font_size + 0.8, color=xtick)
                            ax_s.set_facecolor(ax_face)
                            for lab in ax_s.get_xticklabels(): lab.set_fontsize(font_size); lab.set_color(xtick); lab.set_rotation(20)
                            for lab in ax_s.get_yticklabels(): lab.set_fontsize(font_size - 0.2); lab.set_color(ytick)
                            for sp in ax_s.spines.values(): sp.set_color(spine)
                        if cat_counts:
                            cats = list(cat_counts.keys())[:8]
                            vals = [cat_counts[c] for c in cats]
                            ax_c = fig.add_axes([0.55, y0, 0.38, h])
                            ax_c.bar(cats, vals, color="#60a5fa")
                            ax_c.set_title("Top Categories", fontsize=font_size + 0.8, color=xtick)
                            ax_c.set_facecolor(ax_face)
                            for lab in ax_c.get_xticklabels(): lab.set_fontsize(font_size); lab.set_color(xtick); lab.set_rotation(20)
                            for lab in ax_c.get_yticklabels(): lab.set_fontsize(font_size - 0.2); lab.set_color(ytick)
                            for sp in ax_c.spines.values(): sp.set_color(spine)
                    except Exception as e:
                        logger.warning(f"Failed to generate PDF chart: {e}")
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
        return True
    except (IOError, ValueError) as e:
        logger.error(f"Failed to export PDF: {e}")
        return False

def export_analytics_csv(dest_csv: str) -> bool:
    try:
        with _get_db_connection() as conn:
            runs = pd.read_sql_query("SELECT * FROM analysis_runs ORDER BY run_time DESC", conn)
            issues = pd.read_sql_query("SELECT run_id, severity, category, confidence FROM analysis_issues", conn)
        agg = issues.groupby(["run_id", "severity"]).size().unstack(fill_value=0).reset_index()
        df = runs.merge(agg, left_on="id", right_on="run_id", how="left").drop(columns=["run_id"])
        os.makedirs(os.path.dirname(dest_csv), exist_ok=True)
        df.to_csv(dest_csv, index=False, encoding="utf-8")
        return True
    except (IOError, pd.errors.DatabaseError) as e:
        logger.error(f"export_analytics_csv failed: {e}")
        return False

def export_report_fhir_json(data: dict, fhir_path: str) -> bool:
    try:
        from fhir.resources.bundle import Bundle
        from fhir.resources.diagnosticreport import DiagnosticReport
        from fhir.resources.observation import Observation
        from fhir.resources.codeableconcept import CodeableConcept
        from fhir.resources.coding import Coding
        from fhir.resources.reference import Reference
        from fhir.resources.meta import Meta

        bundle = Bundle(type="collection", entry=[])
        report = DiagnosticReport(
            status="final",
            meta=Meta(profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"]),
            code=CodeableConcept(coding=[Coding(system="http://loinc.org", code="LP296840-5", display="Clinical Note Analysis")]),
            subject=Reference(display="Anonymous Patient"),
            effectiveDateTime=data.get("generated", _now_iso()),
            issued=data.get("generated", _now_iso()),
            performer=[Reference(display="Spec Kit Analyzer")],
            conclusion=f"Compliance Score: {data.get('compliance', {}).get('score', 0.0)}/100.0"
        )
        report.id = "diagnostic-report-1"
        report_ref = f"DiagnosticReport/{report.id}"
        bundle.entry.append({"fullUrl": f"urn:uuid:{report.id}", "resource": report})

        for i, issue in enumerate(data.get("issues", [])):
            obs = Observation(
                id=f"observation-{i+1}", status="final", partOf=[Reference(reference=report_ref)],
                code=CodeableConcept(coding=[Coding(
                    system="http://example.com/speckit-findings",
                    code=str(issue.get("category", "general")).replace(" ", "-"),
                    display=issue.get("title")
                )]),
                subject=Reference(display="Anonymous Patient"), valueString=issue.get("detail"),
                interpretation=[CodeableConcept(coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    code=str(issue.get("severity", "NOTE")).upper(),
                    display=str(issue.get("severity"))
                )])]
            )
            bundle.entry.append({"fullUrl": f"urn:uuid:{obs.id}", "resource": obs})

        os.makedirs(os.path.dirname(fhir_path), exist_ok=True)
        with open(fhir_path, "w", encoding="utf-8") as f:
            f.write(bundle.json(indent=2))
        return True
    except ImportError:
        logger.error("fhir.resources library not found. Please install it to use FHIR export.")
        QMessageBox.warning(None, "FHIR Library Not Found", "The 'fhir.resources' library is required for FHIR export. Please install it (`pip install fhir.resources`).")
        return False
    except (IOError, TypeError) as e:
        logger.error(f"Failed to export FHIR JSON: {e}")
        return False
