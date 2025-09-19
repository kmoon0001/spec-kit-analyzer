import json
import logging
import os
import sqlite3
from typing import Dict, List

import pandas as pd
from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference

logger = logging.getLogger(__name__)

# This is a bit of a hack, but it's the simplest way to get the DB path
# without a major refactor of the settings logic.
_default_db_dir = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData")
DATABASE_PATH = os.getenv("SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db"))

def _get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def run_bias_audit() -> Dict:
    """
    Performs a bias audit on the analysis data.

    Returns:
        A dictionary containing fairness metrics.
    """
    results = {
        "demographic_parity_difference": 0.0,
        "equalized_odds_difference": 0.0,
        "selection_rates": {},
        "error": None,
    }

    try:
        with _get_db_connection() as conn:
            # Query the database to get all analysis runs
            df = pd.read_sql_query("SELECT disciplines, flags FROM analysis_runs", conn)

        if df.empty or 'disciplines' not in df.columns:
            results["error"] = "Not enough data or 'disciplines' column missing."
            return results

        # --- Data Preprocessing ---
        # 1. Filter out runs with no discipline information
        df = df.dropna(subset=['disciplines'])
        if df.empty:
            results["error"] = "No runs with discipline information found."
            return results

        # 2. Create the label (Y): 1 if any flags were found, 0 otherwise.
        df['Y_true'] = (df['flags'] > 0).astype(int)

        # 3. Create the sensitive feature (A): For simplicity, we consider the first
        #    discipline listed for each run. This is a simplification for multi-discipline runs.
        df['A'] = df['disciplines'].apply(lambda x: json.loads(x)[0] if json.loads(x) else 'Unknown')

        # For the audit, we need a "prediction". Since we are auditing the system's
        # output itself, the system's prediction is the same as the true label.
        df['Y_pred'] = df['Y_true']

        y_true = df['Y_true']
        y_pred = df['Y_pred']
        sensitive_features = df['A']

        if len(df['A'].unique()) < 2:
            results["error"] = "Need at least two different groups (disciplines) to perform a bias audit."
            return results

        # --- Calculate Metrics ---
        # 1. Demographic Parity
        dpd = demographic_parity_difference(y_true, sensitive_features=sensitive_features, method='between_groups')
        results["demographic_parity_difference"] = round(dpd, 4)

        # 2. Equalized Odds
        eod = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive_features, method='between_groups')
        results["equalized_odds_difference"] = round(eod, 4)

        # 3. Selection Rates (for visualization)
        rates = df.groupby('A')['Y_true'].value_counts(normalize=True).unstack().fillna(0)
        if 1 in rates.columns:
            results["selection_rates"] = rates[1].to_dict()
        else: # No flags found for any group
            results["selection_rates"] = {group: 0.0 for group in df['A'].unique()}

        return results

    except Exception as e:
        logger.exception(f"Bias audit failed: {e}")
        results["error"] = str(e)
        return results
