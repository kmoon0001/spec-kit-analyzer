import os
import json
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def generate_report_paths() -> Tuple[str, str]:
    from datetime import datetime
    from src.database import ensure_reports_dir_configured, _format_mmddyyyy, _next_report_number
    base = ensure_reports_dir_configured()
    stem = f"{_format_mmddyyyy(datetime.now())}report{_next_report_number()}"
    return os.path.join(base, f"{stem}.pdf"), os.path.join(base, f"{stem}.csv")

def export_report_json(obj: dict, json_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        return False

def export_report_pdf(lines: list[str], pdf_path: str, meta: Optional[dict] = None,
                          chart_data: Optional[dict] = None,
                          sev_counts: Optional[dict] = None,
                          cat_counts: Optional[dict] = None) -> bool:
    # This is a simplified placeholder for the PDF generation logic.
    # In a real scenario, this would use a library like ReportLab or FPDF.
    try:
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write("--- PDF Report ---\n\n")
            if meta:
                for key, value in meta.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            for line in lines:
                f.write(f"{line}\n")
        return True
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        return False
