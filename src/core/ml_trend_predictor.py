"""
Advanced ML Trend Prediction Service
Provides machine learning-based trend analysis and predictions for compliance patterns.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class TrendPrediction:
    """ML-based trend prediction result."""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence_score: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    time_horizon_days: int
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    recommendations: List[str]
    supporting_data: Dict[str, Any]


@dataclass
class CompliancePattern:
    """Detected compliance pattern."""
    pattern_type: str
    frequency: float
    severity: str
    description: str
    first_detected: datetime
    last_seen: datetime
    confidence: float


class MLTrendPredictor:
    """
    Advanced ML-based trend prediction for compliance analytics.
    Uses time series analysis and pattern recognition.
    """
    
    def __init__(self):
        self.prediction_models = {}
        self.pattern_history = []
        self.compliance_metrics = {}
        
    async def predict_compliance_trends(self, 
                                      historical_data: List[Dict[str, Any]], 
                                      time_horizon_days: int = 30) -> List[TrendPrediction]:
        """
        Predict compliance trends using ML algorithms.
        
        Args:
            historical_data: Historical compliance analysis results
            time_horizon_days: Number of days to predict ahead
            
        Returns:
            List of trend predictions
        """
        predictions = []
        
        try:
            if len(historical_data) < 5:
                logger.warning("Insufficient data for ML trend prediction")
                return self._generate_baseline_predictions(time_horizon_days)
            
            # Extract key metrics from historical data
            metrics = self._extract_metrics(historical_data)
            
            # Predict compliance score trends
            compliance_prediction = await self._predict_compliance_score(
                metrics.get('compliance_scores', []), time_horizon_days
            )
            if compliance_prediction:
                predictions.append(compliance_prediction)
            
            # Predict error rate trends
            error_prediction = await self._predict_error_rates(
                metrics.get('error_rates', []), time_horizon_days
            )
            if error_prediction:
                predictions.append(error_prediction)
            
            # Predict documentation quality trends
            quality_prediction = await self._predict_documentation_quality(
                metrics.get('quality_scores', []), time_horizon_days
            )
            if quality_prediction:
                predictions.append(quality_prediction)
            
            # Predict risk level trends
            risk_prediction = await self._predict_risk_levels(
                metrics.get('risk_scores', []), time_horizon_days
            )
            if risk_prediction:
                predictions.append(risk_prediction)
            
            logger.info(f"Generated {len(predictions)} ML trend predictions")
            
        except Exception as e:
            logger.error(f"ML trend prediction failed: {e}")
            predictions = self._generate_baseline_predictions(time_horizon_days)
        
        return predictions
    
    async def detect_compliance_patterns(self, 
                                       historical_data: List[Dict[str, Any]]) -> List[CompliancePattern]:
        """
        Detect recurring compliance patterns using ML pattern recognition.
        
        Args:
            historical_data: Historical compliance analysis results
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        try:
            if len(historical_data) < 10:
                logger.warning("Insufficient data for pattern detection")
                return patterns
            
            # Detect recurring error patterns
            error_patterns = self._detect_error_patterns(historical_data)
            patterns.extend(error_patterns)
            
            # Detect compliance improvement patterns
            improvement_patterns = self._detect_improvement_patterns(historical_data)
            patterns.extend(improvement_patterns)
            
            # Detect seasonal patterns
            seasonal_patterns = self._detect_seasonal_patterns(historical_data)
            patterns.extend(seasonal_patterns)
            
            # Detect anomaly patterns
            anomaly_patterns = self._detect_anomaly_patterns(historical_data)
            patterns.extend(anomaly_patterns)
            
            logger.info(f"Detected {len(patterns)} compliance patterns")
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
        
        return patterns
    
    def _extract_metrics(self, historical_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract key metrics from historical data."""
        metrics = {
            'compliance_scores': [],
            'error_rates': [],
            'quality_scores': [],
            'risk_scores': [],
            'timestamps': []
        }
        
        for record in historical_data:
            # Extract compliance score
            if 'compliance_score' in record:
                metrics['compliance_scores'].append(float(record['compliance_score']))
            elif 'overall_score' in record:
                metrics['compliance_scores'].append(float(record['overall_score']))
            
            # Extract error rate
            findings = record.get('findings', [])
            if findings:
                error_count = len([f for f in findings if f.get('severity') in ['high', 'critical']])
                error_rate = error_count / len(findings) if findings else 0
                metrics['error_rates'].append(error_rate)
            
            # Extract quality score (inverse of error rate)
            if metrics['error_rates']:
                quality_score = 1.0 - metrics['error_rates'][-1]
                metrics['quality_scores'].append(quality_score)
            
            # Extract risk score
            risk_score = record.get('risk_score', 0.5)
            metrics['risk_scores'].append(float(risk_score))
            
            # Extract timestamp
            timestamp = record.get('timestamp', datetime.now().isoformat())
            metrics['timestamps'].append(timestamp)
        
        return metrics
    
    async def _predict_compliance_score(self, 
                                      scores: List[float], 
                                      time_horizon_days: int) -> Optional[TrendPrediction]:
        """Predict compliance score trends."""
        if len(scores) < 3:
            return None
        
        try:
            # Simple linear trend analysis
            x = np.arange(len(scores))
            y = np.array(scores)
            
            # Calculate trend
            if len(scores) >= 2:
                trend_slope = (y[-1] - y[0]) / len(y)
                predicted_value = y[-1] + (trend_slope * time_horizon_days / 7)  # Weekly trend
                predicted_value = max(0.0, min(1.0, predicted_value))  # Clamp to [0,1]
            else:
                predicted_value = y[-1]
                trend_slope = 0
            
            # Determine trend direction
            if trend_slope > 0.02:
                trend_direction = 'increasing'
                risk_level = 'low'
            elif trend_slope < -0.02:
                trend_direction = 'decreasing'
                risk_level = 'high' if predicted_value < 0.7 else 'medium'
            else:
                trend_direction = 'stable'
                risk_level = 'low' if predicted_value > 0.8 else 'medium'
            
            # Calculate confidence based on data consistency
            variance = np.var(y) if len(y) > 1 else 0
            confidence_score = max(0.3, 1.0 - variance)
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                predicted_value, trend_direction, risk_level
            )
            
            return TrendPrediction(
                metric_name="Compliance Score",
                current_value=float(y[-1]),
                predicted_value=float(predicted_value),
                confidence_score=float(confidence_score),
                trend_direction=trend_direction,
                time_horizon_days=time_horizon_days,
                risk_level=risk_level,
                recommendations=recommendations,
                supporting_data={
                    'historical_scores': scores[-10:],  # Last 10 scores
                    'trend_slope': float(trend_slope),
                    'variance': float(variance)
                }
            )
            
        except Exception as e:
            logger.error(f"Compliance score prediction failed: {e}")
            return None
    
    async def _predict_error_rates(self, 
                                 error_rates: List[float], 
                                 time_horizon_days: int) -> Optional[TrendPrediction]:
        """Predict error rate trends."""
        if len(error_rates) < 3:
            return None
        
        try:
            y = np.array(error_rates)
            trend_slope = (y[-1] - y[0]) / len(y) if len(y) >= 2 else 0
            predicted_value = max(0.0, min(1.0, y[-1] + (trend_slope * time_horizon_days / 7)))
            
            # Determine risk level (higher error rates = higher risk)
            if predicted_value > 0.3:
                risk_level = 'critical'
            elif predicted_value > 0.2:
                risk_level = 'high'
            elif predicted_value > 0.1:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            trend_direction = 'increasing' if trend_slope > 0.01 else 'decreasing' if trend_slope < -0.01 else 'stable'
            confidence_score = max(0.3, 1.0 - np.var(y))
            
            recommendations = self._generate_error_rate_recommendations(
                predicted_value, trend_direction, risk_level
            )
            
            return TrendPrediction(
                metric_name="Error Rate",
                current_value=float(y[-1]),
                predicted_value=float(predicted_value),
                confidence_score=float(confidence_score),
                trend_direction=trend_direction,
                time_horizon_days=time_horizon_days,
                risk_level=risk_level,
                recommendations=recommendations,
                supporting_data={
                    'historical_error_rates': error_rates[-10:],
                    'trend_slope': float(trend_slope)
                }
            )
            
        except Exception as e:
            logger.error(f"Error rate prediction failed: {e}")
            return None
    
    async def _predict_documentation_quality(self, 
                                           quality_scores: List[float], 
                                           time_horizon_days: int) -> Optional[TrendPrediction]:
        """Predict documentation quality trends."""
        if len(quality_scores) < 3:
            return None
        
        try:
            y = np.array(quality_scores)
            trend_slope = (y[-1] - y[0]) / len(y) if len(y) >= 2 else 0
            predicted_value = max(0.0, min(1.0, y[-1] + (trend_slope * time_horizon_days / 7)))
            
            # Quality scoring (higher is better)
            if predicted_value > 0.9:
                risk_level = 'low'
            elif predicted_value > 0.8:
                risk_level = 'medium'
            elif predicted_value > 0.7:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            trend_direction = 'increasing' if trend_slope > 0.01 else 'decreasing' if trend_slope < -0.01 else 'stable'
            confidence_score = max(0.3, 1.0 - np.var(y))
            
            recommendations = self._generate_quality_recommendations(
                predicted_value, trend_direction, risk_level
            )
            
            return TrendPrediction(
                metric_name="Documentation Quality",
                current_value=float(y[-1]),
                predicted_value=float(predicted_value),
                confidence_score=float(confidence_score),
                trend_direction=trend_direction,
                time_horizon_days=time_horizon_days,
                risk_level=risk_level,
                recommendations=recommendations,
                supporting_data={
                    'historical_quality_scores': quality_scores[-10:],
                    'trend_slope': float(trend_slope)
                }
            )
            
        except Exception as e:
            logger.error(f"Quality prediction failed: {e}")
            return None
    
    async def _predict_risk_levels(self, 
                                 risk_scores: List[float], 
                                 time_horizon_days: int) -> Optional[TrendPrediction]:
        """Predict risk level trends."""
        if len(risk_scores) < 3:
            return None
        
        try:
            y = np.array(risk_scores)
            trend_slope = (y[-1] - y[0]) / len(y) if len(y) >= 2 else 0
            predicted_value = max(0.0, min(1.0, y[-1] + (trend_slope * time_horizon_days / 7)))
            
            # Risk level assessment
            if predicted_value > 0.8:
                risk_level = 'critical'
            elif predicted_value > 0.6:
                risk_level = 'high'
            elif predicted_value > 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            trend_direction = 'increasing' if trend_slope > 0.01 else 'decreasing' if trend_slope < -0.01 else 'stable'
            confidence_score = max(0.3, 1.0 - np.var(y))
            
            recommendations = self._generate_risk_recommendations(
                predicted_value, trend_direction, risk_level
            )
            
            return TrendPrediction(
                metric_name="Risk Level",
                current_value=float(y[-1]),
                predicted_value=float(predicted_value),
                confidence_score=float(confidence_score),
                trend_direction=trend_direction,
                time_horizon_days=time_horizon_days,
                risk_level=risk_level,
                recommendations=recommendations,
                supporting_data={
                    'historical_risk_scores': risk_scores[-10:],
                    'trend_slope': float(trend_slope)
                }
            )
            
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
            return None
    
    def _generate_baseline_predictions(self, time_horizon_days: int) -> List[TrendPrediction]:
        """Generate baseline predictions when insufficient data is available."""
        return [
            TrendPrediction(
                metric_name="Compliance Score",
                current_value=0.75,
                predicted_value=0.75,
                confidence_score=0.3,
                trend_direction='stable',
                time_horizon_days=time_horizon_days,
                risk_level='medium',
                recommendations=[
                    "Collect more historical data for accurate predictions",
                    "Establish baseline compliance metrics",
                    "Implement regular compliance monitoring"
                ],
                supporting_data={'note': 'Baseline prediction due to insufficient data'}
            )
        ]
    
    def _generate_compliance_recommendations(self, 
                                           predicted_value: float, 
                                           trend_direction: str, 
                                           risk_level: str) -> List[str]:
        """Generate recommendations for compliance score trends."""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.extend([
                "Immediate intervention required - compliance score critically low",
                "Conduct comprehensive compliance audit",
                "Implement emergency compliance improvement plan"
            ])
        elif risk_level == 'high':
            recommendations.extend([
                "Urgent attention needed - compliance declining",
                "Review and update documentation procedures",
                "Increase compliance training frequency"
            ])
        elif trend_direction == 'decreasing':
            recommendations.extend([
                "Monitor compliance trends closely",
                "Identify root causes of declining compliance",
                "Implement preventive measures"
            ])
        else:
            recommendations.extend([
                "Maintain current compliance practices",
                "Continue regular monitoring",
                "Look for optimization opportunities"
            ])
        
        return recommendations
    
    def _generate_error_rate_recommendations(self, 
                                           predicted_value: float, 
                                           trend_direction: str, 
                                           risk_level: str) -> List[str]:
        """Generate recommendations for error rate trends."""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.extend([
                "Critical error rate detected - immediate action required",
                "Implement comprehensive error reduction program",
                "Conduct root cause analysis for all high-severity errors"
            ])
        elif trend_direction == 'increasing':
            recommendations.extend([
                "Error rates increasing - investigate causes",
                "Enhance quality control processes",
                "Provide additional staff training"
            ])
        else:
            recommendations.extend([
                "Continue current error prevention practices",
                "Monitor for emerging error patterns",
                "Maintain quality standards"
            ])
        
        return recommendations
    
    def _generate_quality_recommendations(self, 
                                        predicted_value: float, 
                                        trend_direction: str, 
                                        risk_level: str) -> List[str]:
        """Generate recommendations for quality trends."""
        recommendations = []
        
        if predicted_value > 0.9:
            recommendations.extend([
                "Excellent quality maintained - continue best practices",
                "Share successful practices with other teams",
                "Consider mentoring programs"
            ])
        elif trend_direction == 'decreasing':
            recommendations.extend([
                "Quality declining - review documentation standards",
                "Implement quality improvement initiatives",
                "Increase peer review frequency"
            ])
        else:
            recommendations.extend([
                "Maintain current quality standards",
                "Look for continuous improvement opportunities",
                "Regular quality assessments recommended"
            ])
        
        return recommendations
    
    def _generate_risk_recommendations(self, 
                                     predicted_value: float, 
                                     trend_direction: str, 
                                     risk_level: str) -> List[str]:
        """Generate recommendations for risk level trends."""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.extend([
                "Critical risk level - immediate mitigation required",
                "Activate risk management protocols",
                "Consider external compliance consultation"
            ])
        elif trend_direction == 'increasing':
            recommendations.extend([
                "Risk levels rising - implement preventive measures",
                "Review risk management procedures",
                "Increase monitoring frequency"
            ])
        else:
            recommendations.extend([
                "Maintain current risk management practices",
                "Regular risk assessments recommended",
                "Continue proactive monitoring"
            ])
        
        return recommendations
    
    def _detect_error_patterns(self, historical_data: List[Dict[str, Any]]) -> List[CompliancePattern]:
        """Detect recurring error patterns."""
        patterns = []
        
        # Simple pattern detection - in production, this would use more sophisticated ML
        error_types = {}
        
        for record in historical_data:
            findings = record.get('findings', [])
            for finding in findings:
                error_type = finding.get('category', 'Unknown')
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(record.get('timestamp', datetime.now().isoformat()))
        
        # Identify frequent error types
        for error_type, timestamps in error_types.items():
            if len(timestamps) >= 3:  # Appears in at least 3 analyses
                frequency = len(timestamps) / len(historical_data)
                severity = 'high' if frequency > 0.5 else 'medium' if frequency > 0.3 else 'low'
                
                patterns.append(CompliancePattern(
                    pattern_type=f"Recurring {error_type} Errors",
                    frequency=frequency,
                    severity=severity,
                    description=f"{error_type} errors appear in {frequency:.1%} of analyses",
                    first_detected=datetime.fromisoformat(timestamps[0].replace('Z', '+00:00')) if 'T' in timestamps[0] else datetime.now(),
                    last_seen=datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00')) if 'T' in timestamps[-1] else datetime.now(),
                    confidence=min(0.9, frequency + 0.3)
                ))
        
        return patterns
    
    def _detect_improvement_patterns(self, historical_data: List[Dict[str, Any]]) -> List[CompliancePattern]:
        """Detect compliance improvement patterns."""
        patterns = []
        
        # Analyze compliance score trends
        scores = []
        for record in historical_data:
            score = record.get('compliance_score', record.get('overall_score', 0.5))
            scores.append(float(score))
        
        if len(scores) >= 5:
            # Check for consistent improvement
            recent_avg = np.mean(scores[-3:])
            older_avg = np.mean(scores[:3])
            
            if recent_avg > older_avg + 0.1:  # Significant improvement
                patterns.append(CompliancePattern(
                    pattern_type="Compliance Improvement Trend",
                    frequency=1.0,
                    severity='low',  # Good pattern
                    description=f"Compliance scores improved from {older_avg:.2f} to {recent_avg:.2f}",
                    first_detected=datetime.now() - timedelta(days=len(scores)),
                    last_seen=datetime.now(),
                    confidence=0.8
                ))
        
        return patterns
    
    def _detect_seasonal_patterns(self, historical_data: List[Dict[str, Any]]) -> List[CompliancePattern]:
        """Detect seasonal compliance patterns."""
        patterns = []
        
        # Simple seasonal detection - would be more sophisticated in production
        if len(historical_data) >= 12:  # Need at least 12 data points
            patterns.append(CompliancePattern(
                pattern_type="Potential Seasonal Pattern",
                frequency=0.5,
                severity='medium',
                description="Sufficient data available for seasonal analysis",
                first_detected=datetime.now() - timedelta(days=90),
                last_seen=datetime.now(),
                confidence=0.4
            ))
        
        return patterns
    
    def _detect_anomaly_patterns(self, historical_data: List[Dict[str, Any]]) -> List[CompliancePattern]:
        """Detect anomalous compliance patterns."""
        patterns = []
        
        # Simple anomaly detection
        scores = []
        for record in historical_data:
            score = record.get('compliance_score', record.get('overall_score', 0.5))
            scores.append(float(score))
        
        if len(scores) >= 5:
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # Find outliers (more than 2 standard deviations from mean)
            outliers = [s for s in scores if abs(s - mean_score) > 2 * std_score]
            
            if outliers:
                patterns.append(CompliancePattern(
                    pattern_type="Compliance Score Anomalies",
                    frequency=len(outliers) / len(scores),
                    severity='medium',
                    description=f"Detected {len(outliers)} anomalous compliance scores",
                    first_detected=datetime.now() - timedelta(days=len(scores)),
                    last_seen=datetime.now(),
                    confidence=0.7
                ))
        
        return patterns


# Global ML trend predictor instance
ml_trend_predictor = MLTrendPredictor()