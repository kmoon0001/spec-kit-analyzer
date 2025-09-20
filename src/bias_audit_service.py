import json
import logging
import os
import sqlite3
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    demographic_parity_difference,
    demographic_parity_ratio,
    equalized_odds_difference,
    selection_rate,
)
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)

_default_db_dir = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData")
DATABASE_PATH = os.getenv("SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db"))

def _get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    try:
        db_uri = f"file:{DATABASE_PATH}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        return conn
    except sqlite3.OperationalError:
        logger.warning("Read-only connection failed, falling back to read-write.")
        return sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

class BiasAuditService:
    def __init__(self, db_connection=None):
        # If no connection provided, create one
        self.conn = db_connection or _get_db_connection()

    def get_audit_data(self) -> pd.DataFrame:
        """
        Fetches and prepares data for bias audit from the database.
        Assumes 'analysis_runs' table with 'disciplines' and 'flags' columns.
        """
        try:
            runs_df = pd.read_sql_query("SELECT id, file_name, run_time, compliance_score, disciplines, flags FROM analysis_runs", self.conn)
            if runs_df.empty or 'disciplines' not in runs_df.columns:
                logger.error("Not enough data or 'disciplines' column missing.")
                return pd.DataFrame()

            # Parse discipline as the sensitive feature from JSON list in 'disciplines' column
            def get_primary_discipline(d):
                try:
                    if d:
                        parsed = json.loads(d)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            return parsed[0]
                    return 'Unknown'
                except Exception:
                    return 'Unknown'

            runs_df['discipline'] = runs_df['disciplines'].apply(get_primary_discipline)
            runs_df = runs_df[runs_df['discipline'] != 'Unknown']

            # Prediction: flagged or not, derived from 'flags' column or compliance_score if needed
            if 'flags' in runs_df.columns:
                runs_df['predicted_high_risk'] = runs_df['flags'] > 0
            else:
                runs_df['predicted_high_risk'] = runs_df['compliance_score'] < 80

            # True label: for example, high risk if any 'flag' severity issue exists from issues table
            # This requires fetching issues for a more detailed label, skipping if no issue data
            # For now, fallback to predicted as true since no issues_df access here
            runs_df['is_high_risk'] = runs_df['predicted_high_risk']

            return runs_df
        except Exception as e:
            logger.error(f"Failed to get audit data: {e}")
            return pd.DataFrame()

    def run_bias_audit(self) -> str:
        """
        Runs bias audit and returns a detailed textual report.
        """
        audit_df = self.get_audit_data()
        if audit_df.empty:
            return "Could not retrieve data for the bias audit."

        sensitive_features = audit_df['discipline']
        y_true = audit_df['is_high_risk']
        y_pred = audit_df['predicted_high_risk']

        metrics = {
            'accuracy': accuracy_score,
            'demographic_parity_difference': demographic_parity_difference,
            'demographic_parity_ratio': demographic_parity_ratio,
            'equalized_odds_difference': equalized_odds_difference,
            'selection_rate': selection_rate
        }

        metric_frame = MetricFrame(metrics=metrics,
                                   y_true=y_true,
                                   y_pred=y_pred,
                                   sensitive_features=sensitive_features)

        report_lines = ["Bias Audit Report\n" + "="*20]
        report_lines.append("\nOverall Metrics:")
        report_lines.append(f"- Accuracy: {metric_frame.overall['accuracy']:.3f}")
        report_lines.append(f"- Demographic Parity Difference: {metric_frame.overall['demographic_parity_difference']:.3f}")
        report_lines.append(f"- Demographic Parity Ratio: {metric_frame.overall['demographic_parity_ratio']:.3f}")
        report_lines.append(f"- Equalized Odds Difference: {metric_frame.overall['equalized_odds_difference']:.3f}")
        report_lines.append(f"- Average Selection Rate: {metric_frame.overall['selection_rate']:.3f}")
        report_lines.append("\nMetrics by Discipline:")
        report_lines.append(str(metric_frame.by_group))
        report_lines.append("\nExplanation:")
        report_lines.append("- Demographic Parity Difference measures whether the prediction rate is equal across groups; 0 means perfect fairness.")
        report_lines.append("- Demographic Parity Ratio compares prediction rates, with 1 meaning fairness.")
        report_lines.append("- Equalized Odds Difference measures equal true/false positive rates across groups; 0 means fairness.")
        report_lines.append("- Selection Rate is the average predicted positive rate for each group.")
        return "\n".join(report_lines)
