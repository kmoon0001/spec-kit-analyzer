# Standard library
import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

# Third-party
import pandas as pd

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_default_db_dir = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData")
DATABASE_PATH = os.getenv("SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db"))
REPORTS_DIR = os.getenv("SPEC_KIT_REPORTS", os.path.join(os.path.expanduser("~"), "Documents", "SpecKitReports"))
LOGS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData", "logs")

logger = logging.getLogger(__name__)

def ensure_reports_dir_configured() -> str:
    stored = os.getenv("SPEC_KIT_REPORTS") or get_setting("reports_dir") or REPORTS_DIR
    try:
        os.makedirs(stored, exist_ok=True)
        marker = os.path.join(stored, ".spec_kit_reports")
        if not os.path.exists(marker):
            with open(marker, "w", encoding="utf-8") as m:
                m.write("Managed by SpecKit. Safe to purge generated reports.\n")
    except OSError as e:
        logger.warning(f"Ensure reports dir failed: {e}")
    return stored

# --- Settings persistence (SQLite) ---
def _ensure_directories() -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
        os.makedirs(os.path.abspath(REPORTS_DIR), exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
    except OSError as e:
        logger.warning(f"Failed to ensure directories: {e}")


def _is_valid_sqlite_db(file_path: str) -> bool:
    try:
        if not os.path.exists(file_path):
            return True
        if not os.path.isfile(file_path):
            return False
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header != b"SQLite format 3\x00":
            return False
        with sqlite3.connect(file_path) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            row = cur.fetchone()
            return bool(row and row[0] == "ok")
    except (sqlite3.Error, IOError) as e:
        logger.warning(f"Failed to validate DB file {file_path}: {e}")
        return False


def _backup_corrupt_db(file_path: str) -> None:
    try:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{file_path}.corrupt-{ts}.bak"
        os.replace(file_path, backup_path)
        logger.warning(f"Backed up invalid DB: {backup_path}")
    except OSError as e:
        logger.error(f"Failed to back up invalid DB: {e}")


def _prepare_database_file() -> None:
    try:
        if not _is_valid_sqlite_db(DATABASE_PATH):
            _backup_corrupt_db(DATABASE_PATH)
    except Exception as e:
        logger.error(f"DB preparation failed: {e}")


def _ensure_core_schema(conn: sqlite3.Connection) -> None:
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                file_fingerprint TEXT NOT NULL,
                settings_fingerprint TEXT NOT NULL,
                outputs_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (file_fingerprint, settings_fingerprint)
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"Ensure core schema failed: {e}")

def _ensure_analytics_schema(conn: sqlite3.Connection) -> None:
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                run_time TEXT NOT NULL,
                pages_est INTEGER,
                flags INTEGER,
                wobblers INTEGER,
                suggestions INTEGER,
                notes INTEGER,
                sentences_final INTEGER,
                dedup_removed INTEGER,
                compliance_score REAL,
                mode TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_time ON analysis_runs(run_time)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_file ON analysis_runs(file_name)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                severity TEXT NOT NULL,
                category TEXT,
                title TEXT,
                detail TEXT,
                confidence REAL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs (id) ON DELETE CASCADE
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_run ON analysis_issues(run_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_sev ON analysis_issues(severity)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_cat ON analysis_issues(category)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_snapshots (
                file_fingerprint TEXT NOT NULL,
                settings_fingerprint TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (file_fingerprint, settings_fingerprint)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_time ON analysis_snapshots(created_at)")

        cur.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        if "compliance_score" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN compliance_score REAL")
            logger.info("Upgraded analysis_runs table to include 'compliance_score' column.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviewed_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_issue_id INTEGER NOT NULL,
                user_feedback TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                notes TEXT,
                citation_text TEXT,
                model_prediction TEXT,
                FOREIGN KEY (analysis_issue_id) REFERENCES analysis_issues (id) ON DELETE CASCADE
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_issue ON reviewed_findings(analysis_issue_id)")

        conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"Ensure analytics schema failed: {e}")


def _get_db_connection() -> sqlite3.Connection:
    _ensure_directories()
    _prepare_database_file()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.DatabaseError as e:
        logger.warning(f"sqlite connect failed: {e}; attempting recreate")
        _backup_corrupt_db(DATABASE_PATH)
        conn = sqlite3.connect(DATABASE_PATH)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
        conn.commit()
        _ensure_core_schema(conn)
        _ensure_analytics_schema(conn)
    except sqlite3.Error as e:
        logger.warning(f"SQLite PRAGMA/schema setup partial: {e}")
    return conn


def get_setting(key: str) -> Optional[str]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
    except sqlite3.Error as e:
        logger.warning(f"Failed to get setting {key}: {e}")
        return None


def set_setting(key: str, value: str) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"Failed to set setting {key}: {e}")


def get_bool_setting(key: str, default: bool) -> bool:
    raw = get_setting(key)
    if raw is None:
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")


def set_bool_setting(key: str, value: bool) -> None:
    set_setting(key, "1" if value else "0")


def get_int_setting(key: str, default: int) -> int:
    raw = get_setting(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except (ValueError, TypeError):
        return default


def get_str_setting(key: str, default: str) -> str:
    raw = get_setting(key)
    return default if raw is None else str(raw)


def set_str_setting(key: str, value: str) -> None:
    set_setting(key, value)


# --- Recent files helpers ---
def _load_recent_files() -> list[str]:
    try:
        raw = get_setting("recent_files")
        if not raw:
            return []
        lst = json.loads(raw)
        if not isinstance(lst, list):
            return []
        seen: set[str] = set()
        out: list[str] = []
        for x in lst:
            if isinstance(x, str) and x not in seen:
                seen.add(x)
                out.append(x)
        limit = get_int_setting("recent_max", 20)
        return out[:max(1, limit)]
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to load recent files: {e}")
        return []


def _save_recent_files(files: list[str]) -> None:
    try:
        limit = get_int_setting("recent_max", 20)
        set_setting("recent_files", json.dumps(files[:max(1, limit)], ensure_ascii=False))
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to save recent files: {e}")


def add_recent_file(path: str) -> None:
    if not path:
        return
    files = _load_recent_files()
    files = [p for p in files if p != path]
    files.insert(0, path)
    _save_recent_files(files)


def persist_analysis_run(file_path: str, run_time: str, metrics: dict, issues_scored: list[dict],
                         compliance: dict, mode: str) -> Optional[int]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO analysis_runs (file_name, run_time, pages_est, flags, wobblers, suggestions, notes,
                                           sentences_final, dedup_removed, compliance_score, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                os.path.basename(file_path), run_time,
                int(metrics.get("pages", 0)), int(metrics.get("flags", 0)), int(metrics.get("wobblers", 0)),
                int(metrics.get("suggestions", 0)), int(metrics.get("notes", 0)),
                int(metrics.get("sentences_final", 0)), int(metrics.get("dedup_removed", 0)),
                float(compliance.get("score", 0.0)), mode
            ))
            run_id = int(cur.lastrowid)
            if issues_scored:
                cur.executemany("""
                    INSERT INTO analysis_issues (run_id, severity, category, title, detail, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [(run_id, it.get("severity", ""), it.get("category", ""), it.get("title", ""),
                       it.get("detail", ""), float(it.get("confidence", 0.0))) for it in issues_scored])
            conn.commit()
            return run_id
    except sqlite3.Error as e:
        logger.warning(f"persist_analysis_run failed: {e}")
        return None


def _compute_recent_trends(max_runs: int = 10) -> dict:
    out = {
        "recent_scores": [], "score_delta": 0.0, "avg_score": 0.0,
        "avg_flags": 0.0, "avg_wobblers": 0.0, "avg_suggestions": 0.0,
    }
    try:
        with _get_db_connection() as conn:
            runs = pd.read_sql_query(
                "SELECT compliance_score, flags, wobblers, suggestions FROM analysis_runs ORDER BY run_time ASC", conn
            )
        if runs.empty: return out
        sub = runs.tail(max_runs).copy()
        scores = [float(x) for x in sub["compliance_score"].tolist()]
        out["recent_scores"] = scores
        out["avg_score"] = round(float(sum(scores) / len(scores)), 1) if scores else 0.0
        out["score_delta"] = round((scores[-1] - scores[0]) if len(scores) >= 2 else 0.0, 1)
        out["avg_flags"] = round(float(sub["flags"].mean()), 2)
        out["avg_wobblers"] = round(float(sub["wobblers"].mean()), 2)
        out["avg_suggestions"] = round(float(sub["suggestions"].mean()), 2)
    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        logger.warning(f"Failed to compute recent trends: {e}")
    return out


# --- Caching helpers ---
def _file_fingerprint(path: str) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        st = os.stat(path)
        h.update(str(st.st_size).encode())
        h.update(str(int(st.st_mtime)).encode())
        return h.hexdigest()
    except (IOError, OSError):
        return ""

def _settings_fingerprint(scrub: bool, review_mode: str, dedup: str) -> str:
    key_parts = {
        "scrub": "1" if scrub else "0",
        "review_mode": review_mode,
        "dedup": dedup,
        "ocr_lang": get_str_setting("ocr_lang", "eng"),
        "logic_v": "4",
    }
    s = json.dumps(key_parts, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _load_cached_outputs(file_fp: str, settings_fp: str) -> Optional[dict]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT outputs_json FROM analysis_cache WHERE file_fingerprint=? AND settings_fingerprint=?",
                        (file_fp, settings_fp))
            row = cur.fetchone()
            if not row: return None
            return json.loads(row[0])
    except (sqlite3.Error, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load cached outputs: {e}")
        return None


def _save_cached_outputs(file_fp: str, settings_fp: str, outputs: dict) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO analysis_cache (file_fingerprint, settings_fingerprint, outputs_json, created_at) VALUES (?, ?, ?, ?)",
                (file_fp, settings_fp, json.dumps(outputs, ensure_ascii=False),
                 datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"Failed to save cached outputs: {e}")


def _load_last_snapshot(file_fp: str, settings_fp: str) -> Optional[dict]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT summary_json FROM analysis_snapshots WHERE file_fingerprint = ? AND settings_fingerprint = ?",
                        (file_fp, settings_fp))
            row = cur.fetchone()
            if not row: return None
            return json.loads(row[0])
    except (sqlite3.Error, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load last snapshot: {e}")
        return None


def _save_snapshot(file_fp: str, settings_fp: str, payload: dict) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_snapshots (
                    file_fingerprint TEXT NOT NULL,
                    settings_fingerprint TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (file_fingerprint, settings_fingerprint)
                )
            """)
            cur.execute("""
                INSERT OR REPLACE INTO analysis_snapshots
                (file_fingerprint, settings_fingerprint, summary_json, created_at)
                VALUES (?,?,?,?)
            """, (file_fp, settings_fp, json.dumps(payload, ensure_ascii=False),
                  datetime.now().isoformat(timespec="seconds")))
            conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"Failed to save snapshot: {e}")
