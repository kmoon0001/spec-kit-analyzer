import json
import logging
import os
import sqlite3
from typing import Dict

import pandas as pd
from fairlearn.metrics import (demographic_parity_difference,
                               demographic_parity_ratio, selection_rate)

logger = logging.getLogger(__name__)

_default_db_dir = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData")
DATABASE_PATH = os.getenv("SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db"))

def _get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    try:
        # Use a URI to connect in read-only mode to prevent accidental writes
        db_uri = f"file:{DATABASE_PATH}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        return conn
    except sqlite3.OperationalError:
        # Fallback for older sqlite versions that don't support URI
        logger.warning("Read-only connection failed, falling back to read-write.")
        return sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def run_bias_audit() -> Dict:
    """
    Performs a bias audit on the analysis data.

    Since there is no independent ground truth, this audit focuses on
    disparities in selection rate (i.e., demographic parity).

    Returns:
        A dictionary containing fairness metrics.
    """
    results = {
        "demographic_parity_difference": 0.0,
        "demographic_parity_ratio": 0.0,
        "selection_rates": {},
        "error": None,
    }

    try:
        with _get_db_connection() as conn:
            df = pd.read_sql_query("SELECT disciplines, flags FROM analysis_runs", conn)

        if df.empty or 'disciplines' not in df.columns:
            results["error"] = "Not enough data or 'disciplines' column missing."
            return results

        df = df.dropna(subset=['disciplines'])
        if df.empty:
            results["error"] = "No runs with discipline information found."
            return results

        # The "prediction" (y_pred) is whether the system generated a flag.
        df['y_pred'] = (df['flags'] > 0).astype(int)
        # The sensitive feature is the primary discipline.
        df['A'] = df['disciplines'].apply(lambda x: json.loads(x)[0] if (x and json.loads(x)) else 'Unknown')
        df = df[df['A'] != 'Unknown']

        if len(df['A'].unique()) < 2:
            results["error"] = "Need at least two different discipline groups to perform a bias audit."
            return results

        y_pred = df['y_pred']
        sensitive_features = df['A']

        # For selection_rate based metrics, y_true is ignored, but required by the function signature.
        # It's common practice to pass y_pred as a placeholder.
        y_true_placeholder = y_pred

        # --- Calculate Metrics ---
        results["demographic_parity_difference"] = demographic_parity_difference(
            y_true_placeholder, y_pred, sensitive_features=sensitive_features
        )
        results["demographic_parity_ratio"] = demographic_parity_ratio(
            y_true_placeholder, y_pred, sensitive_features=sensitive_features
        )

        # --- Calculate selection rate for each group for visualization ---
        rates = {}
        for group in sensitive_features.unique():
            mask = sensitive_features == group
            rates[group] = selection_rate(y_true_placeholder[mask], y_pred[mask])
        results["selection_rates"] = rates

        return results

    except Exception as e:
        logger.exception(f"Bias audit failed: {e}")
        results["error"] = str(e)
        return results
