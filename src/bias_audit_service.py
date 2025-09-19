import pandas as pd
from fairlearn.metrics import MetricFrame, demographic_parity_difference, equalized_odds_difference
from sklearn.metrics import accuracy_score
import logging

logger = logging.getLogger(__name__)

class BiasAuditService:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_audit_data(self) -> pd.DataFrame:
        """
        Fetches and prepares the data needed for a bias audit from the database.
        This function assumes that 'analysis_runs' and 'analysis_issues' tables exist.
        """
        try:
            # Fetch all analysis runs
            runs_df = pd.read_sql_query("SELECT id, file_name, run_time, compliance_score FROM analysis_runs", self.conn)

            # Fetch all issues
            issues_df = pd.read_sql_query("SELECT run_id, severity, category FROM analysis_issues", self.conn)

            # For this audit, we'll define a simple "high-risk" label.
            # A run is high-risk if it has at least one 'flag' severity issue.
            high_risk_runs = issues_df[issues_df['severity'] == 'flag']['run_id'].unique()
            runs_df['is_high_risk'] = runs_df['id'].isin(high_risk_runs)

            # We need a sensitive feature to audit. Let's use the discipline,
            # which we can infer from the filename for this example.
            def get_discipline_from_filename(name):
                if 'pt' in name.lower():
                    return 'PT'
                if 'ot' in name.lower():
                    return 'OT'
                if 'slp' in name.lower():
                    return 'SLP'
                return 'Unknown'

            runs_df['discipline'] = runs_df['file_name'].apply(get_discipline_from_filename)

            # For the purpose of this audit, we'll create a mock "prediction".
            # Let's say our "model" predicts a document is high-risk if its compliance score is below 80.
            runs_df['predicted_high_risk'] = runs_df['compliance_score'] < 80

            # Filter out runs where the discipline is unknown
            audit_df = runs_df[runs_df['discipline'] != 'Unknown']

            return audit_df

        except Exception as e:
            logger.error(f"Failed to get data for bias audit: {e}")
            return pd.DataFrame()

    def run_bias_audit(self):
        """
        Performs a bias audit using the fetched data and returns a summary of the results.
        """
        audit_df = self.get_audit_data()

        if audit_df.empty:
            return "Could not retrieve data for the bias audit."

        # Define the sensitive features, true labels, and predicted labels
        sensitive_features = audit_df['discipline']
        y_true = audit_df['is_high_risk']
        y_pred = audit_df['predicted_high_risk']

        # Define the metrics to compute
        metrics = {
            'accuracy': accuracy_score,
            'demographic_parity_difference': demographic_parity_difference,
            'equalized_odds_difference': equalized_odds_difference
        }

        # Use MetricFrame to compute the metrics across discipline groups
        metric_frame = MetricFrame(metrics=metrics,
                                   y_true=y_true,
                                   y_pred=y_pred,
                                   sensitive_features=sensitive_features)

        # Build a results report
        report_lines = ["Bias Audit Report\n" + "="*20]
        report_lines.append("\nOverall Metrics:")
        report_lines.append(f"- Accuracy: {metric_frame.overall['accuracy']:.3f}")
        report_lines.append(f"- Demographic Parity Difference: {metric_frame.overall['demographic_parity_difference']:.3f}")
        report_lines.append(f"- Equalized Odds Difference: {metric_frame.overall['equalized_odds_difference']:.3f}")

        report_lines.append("\nMetrics by Discipline:")
        report_lines.append(str(metric_frame.by_group))

        report_lines.append("\nExplanation:")
        report_lines.append("- **Demographic Parity Difference:** Measures whether the model's prediction rate is the same across different subgroups. A value of 0 indicates perfect fairness.")
        report_lines.append("- **Equalized Odds Difference:** Measures whether the model has the same true positive rate and false positive rate across subgroups. A value of 0 indicates perfect fairness.")

        return "\n".join(report_lines)
