"""Human-in-the-Loop Feedback System for Clinical Compliance Analysis.

This module implements a comprehensive feedback system that allows clinicians
to provide feedback on AI findings, enabling continuous improvement and
validation of the analysis system.

Features:
- Interactive feedback collection
- Feedback validation and processing
- Model adaptation based on feedback
- Feedback analytics and reporting
- Integration with ensemble optimization
- Feedback-driven confidence calibration
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be provided."""
    CORRECTION = "correction"  # Correcting an AI finding
    VALIDATION = "validation"  # Validating an AI finding
    IMPROVEMENT = "improvement"  # Suggesting improvements
    CLARIFICATION = "clarification"  # Requesting clarification
    DISAGREEMENT = "disagreement"  # Disagreeing with AI assessment


class FeedbackStatus(Enum):
    """Status of feedback processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    APPLIED = "applied"
    REJECTED = "rejected"


class FeedbackPriority(Enum):
    """Priority levels for feedback."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackItem:
    """Individual feedback item."""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    analysis_id: str
    finding_id: Optional[str] = None
    feedback_type: FeedbackType = FeedbackType.CORRECTION
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    content: str = ""
    original_finding: Optional[Dict[str, Any]] = None
    suggested_correction: Optional[Dict[str, Any]] = None
    confidence_rating: Optional[float] = None  # User's confidence in their feedback
    timestamp: datetime = field(default_factory=datetime.now)
    status: FeedbackStatus = FeedbackStatus.PENDING
    processed_by: Optional[str] = None
    processing_notes: Optional[str] = None
    impact_score: float = 0.0  # Calculated impact on model performance


@dataclass
class FeedbackBatch:
    """Batch of feedback items for processing."""
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    analysis_id: str
    feedback_items: List[FeedbackItem] = field(default_factory=list)
    batch_timestamp: datetime = field(default_factory=datetime.now)
    status: FeedbackStatus = FeedbackStatus.PENDING
    processing_priority: FeedbackPriority = FeedbackPriority.MEDIUM


@dataclass
class FeedbackMetrics:
    """Metrics for feedback analysis."""
    total_feedback_count: int = 0
    feedback_by_type: Dict[str, int] = field(default_factory=dict)
    feedback_by_priority: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0
    processing_time_avg: float = 0.0
    impact_score_avg: float = 0.0
    model_improvement_score: float = 0.0


class HumanFeedbackSystem:
    """Human-in-the-loop feedback system for clinical compliance analysis.

    Enables continuous improvement through clinician feedback on AI findings.
    """

    def __init__(self, storage_path: str = "feedback_storage", enable_learning: bool = True):
        """Initialize the human feedback system.

        Args:
            storage_path: Path to store feedback data
            enable_learning: Whether to enable model adaptation from feedback
        """
        self.storage_path = Path(storage_path)
        self.enable_learning = enable_learning
        self.storage_path.mkdir(exist_ok=True)

        # Feedback storage
        self.feedback_storage: Dict[str, FeedbackItem] = {}
        self.feedback_batches: Dict[str, FeedbackBatch] = {}

        # Learning and adaptation
        self.feedback_history: List[FeedbackItem] = []
        self.model_adaptations: Dict[str, Any] = {}
        self.confidence_calibration: Dict[str, float] = {}

        # Processing queues
        self.pending_feedback: List[str] = []
        self.processing_feedback: List[str] = []

        # Metrics
        self.feedback_metrics = FeedbackMetrics()

        # Configuration
        self.config = {
            'min_feedback_for_adaptation': 10,
            'confidence_threshold': 0.7,
            'impact_threshold': 0.5,
            'batch_size': 5,
            'processing_timeout': 300,  # 5 minutes
            'retention_days': 90
        }

        logger.info("Human feedback system initialized with learning=%s", enable_learning)

    async def submit_feedback(
        self,
        user_id: int,
        analysis_id: str,
        feedback_type: FeedbackType,
        content: str,
        finding_id: Optional[str] = None,
        original_finding: Optional[Dict[str, Any]] = None,
        suggested_correction: Optional[Dict[str, Any]] = None,
        confidence_rating: Optional[float] = None,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM
    ) -> str:
        """Submit feedback for an analysis.

        Args:
            user_id: ID of the user submitting feedback
            analysis_id: ID of the analysis being feedback on
            feedback_type: Type of feedback
            content: Feedback content
            finding_id: Specific finding ID (if applicable)
            original_finding: Original AI finding
            suggested_correction: Suggested correction
            confidence_rating: User's confidence in their feedback
            priority: Priority level

        Returns:
            Feedback ID
        """
        try:
            # Create feedback item
            feedback_item = FeedbackItem(
                user_id=user_id,
                analysis_id=analysis_id,
                finding_id=finding_id,
                feedback_type=feedback_type,
                priority=priority,
                content=content,
                original_finding=original_finding,
                suggested_correction=suggested_correction,
                confidence_rating=confidence_rating
            )

            # Calculate impact score
            feedback_item.impact_score = await self._calculate_impact_score(feedback_item)

            # Store feedback
            self.feedback_storage[feedback_item.feedback_id] = feedback_item
            self.feedback_history.append(feedback_item)

            # Add to processing queue
            self.pending_feedback.append(feedback_item.feedback_id)

            # Save to persistent storage
            await self._save_feedback_item(feedback_item)

            logger.info("Feedback submitted: %s (type: %s, priority: %s)",
                       feedback_item.feedback_id, feedback_type.value, priority.value)

            # Trigger batch processing if enough feedback
            if len(self.pending_feedback) >= self.config['batch_size']:
                await self._process_feedback_batch()

            return feedback_item.feedback_id

        except Exception as e:
            logger.exception("Failed to submit feedback: %s", e)
            raise

    async def get_feedback_for_analysis(
        self,
        analysis_id: str,
        user_id: Optional[int] = None
    ) -> List[FeedbackItem]:
        """Get all feedback for a specific analysis.

        Args:
            analysis_id: Analysis ID
            user_id: Optional user ID filter

        Returns:
            List of feedback items
        """
        feedback_items = []

        for feedback_id, feedback_item in self.feedback_storage.items():
            if feedback_item.analysis_id == analysis_id:
                if user_id is None or feedback_item.user_id == user_id:
                    feedback_items.append(feedback_item)

        return sorted(feedback_items, key=lambda x: x.timestamp, reverse=True)

    async def process_feedback_item(
        self,
        feedback_id: str,
        processor_id: str,
        processing_notes: Optional[str] = None
    ) -> bool:
        """Process a specific feedback item.

        Args:
            feedback_id: Feedback ID to process
            processor_id: ID of the processor
            processing_notes: Optional processing notes

        Returns:
            True if processing successful
        """
        try:
            if feedback_id not in self.feedback_storage:
                logger.warning("Feedback item not found: %s", feedback_id)
                return False

            feedback_item = self.feedback_storage[feedback_id]

            # Update status
            feedback_item.status = FeedbackStatus.PROCESSING
            feedback_item.processed_by = processor_id
            feedback_item.processing_notes = processing_notes

            # Process based on feedback type
            if feedback_item.feedback_type == FeedbackType.CORRECTION:
                await self._process_correction_feedback(feedback_item)
            elif feedback_item.feedback_type == FeedbackType.VALIDATION:
                await self._process_validation_feedback(feedback_item)
            elif feedback_item.feedback_type == FeedbackType.IMPROVEMENT:
                await self._process_improvement_feedback(feedback_item)
            elif feedback_item.feedback_type == FeedbackType.CLARIFICATION:
                await self._process_clarification_feedback(feedback_item)
            elif feedback_item.feedback_type == FeedbackType.DISAGREEMENT:
                await self._process_disagreement_feedback(feedback_item)

            # Update status
            feedback_item.status = FeedbackStatus.PROCESSED

            # Apply model adaptations if learning is enabled
            if self.enable_learning:
                await self._apply_model_adaptations(feedback_item)

            # Update metrics
            await self._update_feedback_metrics()

            # Save updated feedback
            await self._save_feedback_item(feedback_item)

            logger.info("Feedback processed successfully: %s", feedback_id)
            return True

        except Exception as e:
            logger.exception("Failed to process feedback item %s: %s", feedback_id, e)
            if feedback_id in self.feedback_storage:
                self.feedback_storage[feedback_id].status = FeedbackStatus.REJECTED
            return False

    async def _process_correction_feedback(self, feedback_item: FeedbackItem) -> None:
        """Process correction feedback."""
        if not feedback_item.suggested_correction:
            logger.warning("No suggested correction provided for feedback %s", feedback_item.feedback_id)
            return

        # Validate correction
        correction_valid = await self._validate_correction(
            feedback_item.original_finding,
            feedback_item.suggested_correction
        )

        if correction_valid:
            # Update confidence calibration
            await self._update_confidence_calibration(feedback_item)

            # Record adaptation
            self.model_adaptations[feedback_item.feedback_id] = {
                'type': 'correction',
                'original': feedback_item.original_finding,
                'corrected': feedback_item.suggested_correction,
                'impact_score': feedback_item.impact_score,
                'timestamp': feedback_item.timestamp
            }

            logger.info("Correction feedback processed: %s", feedback_item.feedback_id)

    async def _process_validation_feedback(self, feedback_item: FeedbackItem) -> None:
        """Process validation feedback."""
        # Update confidence calibration based on validation
        if feedback_item.confidence_rating is not None:
            await self._update_confidence_calibration(feedback_item)

        # Record validation
        self.model_adaptations[feedback_item.feedback_id] = {
            'type': 'validation',
            'finding': feedback_item.original_finding,
            'user_confidence': feedback_item.confidence_rating,
            'impact_score': feedback_item.impact_score,
            'timestamp': feedback_item.timestamp
        }

        logger.info("Validation feedback processed: %s", feedback_item.feedback_id)

    async def _process_improvement_feedback(self, feedback_item: FeedbackItem) -> None:
        """Process improvement feedback."""
        # Analyze improvement suggestions
        improvement_score = await self._analyze_improvement_suggestions(feedback_item.content)

        # Record improvement
        self.model_adaptations[feedback_item.feedback_id] = {
            'type': 'improvement',
            'suggestions': feedback_item.content,
            'improvement_score': improvement_score,
            'impact_score': feedback_item.impact_score,
            'timestamp': feedback_item.timestamp
        }

        logger.info("Improvement feedback processed: %s", feedback_item.feedback_id)

    async def _process_clarification_feedback(self, feedback_item: FeedbackItem) -> None:
        """Process clarification feedback."""
        # Generate clarification response
        clarification_response = await self._generate_clarification_response(feedback_item)

        # Record clarification
        self.model_adaptations[feedback_item.feedback_id] = {
            'type': 'clarification',
            'question': feedback_item.content,
            'response': clarification_response,
            'impact_score': feedback_item.impact_score,
            'timestamp': feedback_item.timestamp
        }

        logger.info("Clarification feedback processed: %s", feedback_item.feedback_id)

    async def _process_disagreement_feedback(self, feedback_item: FeedbackItem) -> None:
        """Process disagreement feedback."""
        # Analyze disagreement
        disagreement_analysis = await self._analyze_disagreement(feedback_item)

        # Update confidence calibration
        await self._update_confidence_calibration(feedback_item)

        # Record disagreement
        self.model_adaptations[feedback_item.feedback_id] = {
            'type': 'disagreement',
            'analysis': disagreement_analysis,
            'impact_score': feedback_item.impact_score,
            'timestamp': feedback_item.timestamp
        }

        logger.info("Disagreement feedback processed: %s", feedback_item.feedback_id)

    async def _calculate_impact_score(self, feedback_item: FeedbackItem) -> float:
        """Calculate impact score for feedback."""
        impact_score = 0.0

        # Base impact by feedback type
        type_impact = {
            FeedbackType.CORRECTION: 0.8,
            FeedbackType.VALIDATION: 0.6,
            FeedbackType.IMPROVEMENT: 0.7,
            FeedbackType.CLARIFICATION: 0.4,
            FeedbackType.DISAGREEMENT: 0.9
        }
        impact_score += type_impact.get(feedback_item.feedback_type, 0.5)

        # Priority impact
        priority_impact = {
            FeedbackPriority.LOW: 0.2,
            FeedbackPriority.MEDIUM: 0.5,
            FeedbackPriority.HIGH: 0.8,
            FeedbackPriority.CRITICAL: 1.0
        }
        impact_score += priority_impact.get(feedback_item.priority, 0.5)

        # Confidence impact
        if feedback_item.confidence_rating is not None:
            impact_score += feedback_item.confidence_rating * 0.3

        # Content length impact (more detailed feedback = higher impact)
        content_length = len(feedback_item.content.split())
        impact_score += min(0.2, content_length / 100.0)

        return min(1.0, impact_score)

    async def _validate_correction(
        self,
        original_finding: Optional[Dict[str, Any]],
        suggested_correction: Optional[Dict[str, Any]]
    ) -> bool:
        """Validate a suggested correction."""
        if not original_finding or not suggested_correction:
            return False

        # Basic validation checks
        required_fields = ['issue_title', 'severity', 'recommendation']

        for field in required_fields:
            if field not in suggested_correction:
                logger.warning("Missing required field in correction: %s", field)
                return False

        # Check for reasonable changes
        if original_finding.get('issue_title') == suggested_correction.get('issue_title'):
            logger.warning("No change in issue title")
            return False

        return True

    async def _update_confidence_calibration(self, feedback_item: FeedbackItem) -> None:
        """Update confidence calibration based on feedback."""
        if not feedback_item.confidence_rating:
            return

        # Update calibration for this type of finding
        finding_type = feedback_item.original_finding.get('issue_title', 'unknown') if feedback_item.original_finding else 'unknown'

        if finding_type not in self.confidence_calibration:
            self.confidence_calibration[finding_type] = []

        self.confidence_calibration[finding_type].append({
            'user_confidence': feedback_item.confidence_rating,
            'ai_confidence': feedback_item.original_finding.get('confidence', 0.5) if feedback_item.original_finding else 0.5,
            'timestamp': feedback_item.timestamp
        })

        # Keep only recent calibrations
        if len(self.confidence_calibration[finding_type]) > 100:
            self.confidence_calibration[finding_type] = self.confidence_calibration[finding_type][-50:]

    async def _analyze_improvement_suggestions(self, content: str) -> float:
        """Analyze improvement suggestions and score them."""
        # Simple scoring based on content analysis
        score = 0.0

        # Check for specific improvement keywords
        improvement_keywords = [
            'accuracy', 'precision', 'recall', 'performance', 'efficiency',
            'speed', 'quality', 'reliability', 'consistency', 'validation'
        ]

        content_lower = content.lower()
        for keyword in improvement_keywords:
            if keyword in content_lower:
                score += 0.1

        # Check for actionable suggestions
        action_keywords = ['should', 'could', 'would', 'recommend', 'suggest', 'improve']
        for keyword in action_keywords:
            if keyword in content_lower:
                score += 0.05

        return min(1.0, score)

    async def _generate_clarification_response(self, feedback_item: FeedbackItem) -> str:
        """Generate clarification response for feedback."""
        # Simple clarification response generation
        if feedback_item.original_finding:
            finding_title = feedback_item.original_finding.get('issue_title', 'the finding')
            return f"Thank you for requesting clarification about {finding_title}. " \
                   f"The AI identified this issue based on compliance guidelines. " \
                   f"Would you like more specific details about the underlying rules or recommendations?"
        else:
            return "Thank you for your question. Could you please provide more context " \
                   "about what specific aspect you'd like clarified?"

    async def _analyze_disagreement(self, feedback_item: FeedbackItem) -> Dict[str, Any]:
        """Analyze disagreement feedback."""
        analysis = {
            'disagreement_type': 'unknown',
            'severity': 'medium',
            'potential_causes': [],
            'recommendations': []
        }

        content_lower = feedback_item.content.lower()

        # Analyze disagreement type
        if 'wrong' in content_lower or 'incorrect' in content_lower:
            analysis['disagreement_type'] = 'factual'
        elif 'unfair' in content_lower or 'biased' in content_lower:
            analysis['disagreement_type'] = 'bias'
        elif 'incomplete' in content_lower or 'missing' in content_lower:
            analysis['disagreement_type'] = 'completeness'
        elif 'too strict' in content_lower or 'too lenient' in content_lower:
            analysis['disagreement_type'] = 'severity'

        # Analyze severity
        if any(word in content_lower for word in ['critical', 'serious', 'major']):
            analysis['severity'] = 'high'
        elif any(word in content_lower for word in ['minor', 'small', 'slight']):
            analysis['severity'] = 'low'

        # Generate recommendations
        if analysis['disagreement_type'] == 'factual':
            analysis['recommendations'].append('Review training data for accuracy')
        elif analysis['disagreement_type'] == 'bias':
            analysis['recommendations'].append('Implement bias detection and mitigation')
        elif analysis['disagreement_type'] == 'completeness':
            analysis['recommendations'].append('Expand analysis criteria')

        return analysis

    async def _apply_model_adaptations(self, feedback_item: FeedbackItem) -> None:
        """Apply model adaptations based on feedback."""
        if feedback_item.impact_score < self.config['impact_threshold']:
            return

        # Apply adaptations based on feedback type
        if feedback_item.feedback_type == FeedbackType.CORRECTION:
            await self._apply_correction_adaptation(feedback_item)
        elif feedback_item.feedback_type == FeedbackType.VALIDATION:
            await self._apply_validation_adaptation(feedback_item)
        elif feedback_item.feedback_type == FeedbackType.IMPROVEMENT:
            await self._apply_improvement_adaptation(feedback_item)
        elif feedback_item.feedback_type == FeedbackType.DISAGREEMENT:
            await self._apply_disagreement_adaptation(feedback_item)

    async def _apply_correction_adaptation(self, feedback_item: FeedbackItem) -> None:
        """Apply correction-based model adaptation."""
        # Update model weights based on correction
        if feedback_item.suggested_correction:
            # This would integrate with the ensemble optimizer
            logger.info("Applying correction adaptation for feedback %s", feedback_item.feedback_id)

    async def _apply_validation_adaptation(self, feedback_item: FeedbackItem) -> None:
        """Apply validation-based model adaptation."""
        # Update confidence calibration
        logger.info("Applying validation adaptation for feedback %s", feedback_item.feedback_id)

    async def _apply_improvement_adaptation(self, feedback_item: FeedbackItem) -> None:
        """Apply improvement-based model adaptation."""
        # Update model parameters based on improvement suggestions
        logger.info("Applying improvement adaptation for feedback %s", feedback_item.feedback_id)

    async def _apply_disagreement_adaptation(self, feedback_item: FeedbackItem) -> None:
        """Apply disagreement-based model adaptation."""
        # Adjust model behavior based on disagreement analysis
        logger.info("Applying disagreement adaptation for feedback %s", feedback_item.feedback_id)

    async def _process_feedback_batch(self) -> None:
        """Process a batch of pending feedback."""
        if not self.pending_feedback:
            return

        # Create batch
        batch_items = self.pending_feedback[:self.config['batch_size']]
        batch = FeedbackBatch(
            feedback_items=[self.feedback_storage[fid] for fid in batch_items if fid in self.feedback_storage]
        )

        self.feedback_batches[batch.batch_id] = batch
        self.pending_feedback = self.pending_feedback[self.config['batch_size']:]

        # Process batch
        logger.info("Processing feedback batch %s with %d items", batch.batch_id, len(batch.feedback_items))

        for feedback_item in batch.feedback_items:
            await self.process_feedback_item(feedback_item.feedback_id, "batch_processor")

    async def _update_feedback_metrics(self) -> None:
        """Update feedback metrics."""
        total_count = len(self.feedback_history)

        if total_count == 0:
            return

        # Count by type
        type_counts = {}
        priority_counts = {}
        confidence_sum = 0.0
        impact_sum = 0.0

        for feedback in self.feedback_history:
            # Type counts
            type_name = feedback.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Priority counts
            priority_name = feedback.priority.value
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

            # Confidence and impact sums
            if feedback.confidence_rating:
                confidence_sum += feedback.confidence_rating
            impact_sum += feedback.impact_score

        # Update metrics
        self.feedback_metrics.total_feedback_count = total_count
        self.feedback_metrics.feedback_by_type = type_counts
        self.feedback_metrics.feedback_by_priority = priority_counts
        self.feedback_metrics.average_confidence = confidence_sum / max(1, sum(1 for f in self.feedback_history if f.confidence_rating))
        self.feedback_metrics.impact_score_avg = impact_sum / total_count

    async def _save_feedback_item(self, feedback_item: FeedbackItem) -> None:
        """Save feedback item to persistent storage."""
        try:
            file_path = self.storage_path / f"feedback_{feedback_item.feedback_id}.json"

            # Convert to JSON-serializable format
            feedback_data = {
                'feedback_id': feedback_item.feedback_id,
                'user_id': feedback_item.user_id,
                'analysis_id': feedback_item.analysis_id,
                'finding_id': feedback_item.finding_id,
                'feedback_type': feedback_item.feedback_type.value,
                'priority': feedback_item.priority.value,
                'content': feedback_item.content,
                'original_finding': feedback_item.original_finding,
                'suggested_correction': feedback_item.suggested_correction,
                'confidence_rating': feedback_item.confidence_rating,
                'timestamp': feedback_item.timestamp.isoformat(),
                'status': feedback_item.status.value,
                'processed_by': feedback_item.processed_by,
                'processing_notes': feedback_item.processing_notes,
                'impact_score': feedback_item.impact_score
            }

            with open(file_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)

        except Exception as e:
            logger.error("Failed to save feedback item %s: %s", feedback_item.feedback_id, e)

    async def get_feedback_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get feedback analytics for a date range.

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Analytics data
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        # Filter feedback by date range
        filtered_feedback = [
            f for f in self.feedback_history
            if start_date <= f.timestamp <= end_date
        ]

        # Calculate analytics
        analytics = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_feedback': len(filtered_feedback),
            'feedback_by_type': {},
            'feedback_by_priority': {},
            'average_confidence': 0.0,
            'average_impact_score': 0.0,
            'processing_stats': {
                'pending': 0,
                'processing': 0,
                'processed': 0,
                'rejected': 0
            },
            'top_issues': [],
            'user_engagement': {}
        }

        if not filtered_feedback:
            return analytics

        # Calculate metrics
        type_counts = {}
        priority_counts = {}
        confidence_sum = 0.0
        impact_sum = 0.0
        status_counts = {'pending': 0, 'processing': 0, 'processed': 0, 'rejected': 0}
        user_counts = {}

        for feedback in filtered_feedback:
            # Type counts
            type_name = feedback.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Priority counts
            priority_name = feedback.priority.value
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

            # Confidence and impact
            if feedback.confidence_rating:
                confidence_sum += feedback.confidence_rating
            impact_sum += feedback.impact_score

            # Status counts
            status_counts[feedback.status.value] += 1

            # User engagement
            user_counts[feedback.user_id] = user_counts.get(feedback.user_id, 0) + 1

        # Update analytics
        analytics['feedback_by_type'] = type_counts
        analytics['feedback_by_priority'] = priority_counts
        analytics['average_confidence'] = confidence_sum / max(1, sum(1 for f in filtered_feedback if f.confidence_rating))
        analytics['average_impact_score'] = impact_sum / len(filtered_feedback)
        analytics['processing_stats'] = status_counts
        analytics['user_engagement'] = user_counts

        return analytics

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get current feedback statistics."""
        return {
            'total_feedback': len(self.feedback_history),
            'pending_feedback': len(self.pending_feedback),
            'processing_feedback': len(self.processing_feedback),
            'feedback_metrics': {
                'total_feedback_count': self.feedback_metrics.total_feedback_count,
                'feedback_by_type': self.feedback_metrics.feedback_by_type,
                'feedback_by_priority': self.feedback_metrics.feedback_by_priority,
                'average_confidence': self.feedback_metrics.average_confidence,
                'impact_score_avg': self.feedback_metrics.impact_score_avg
            },
            'model_adaptations': len(self.model_adaptations),
            'confidence_calibration_types': len(self.confidence_calibration),
            'learning_enabled': self.enable_learning
        }

    async def cleanup_old_feedback(self) -> int:
        """Clean up old feedback data."""
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])

        removed_count = 0
        feedback_to_remove = []

        for feedback_id, feedback_item in self.feedback_storage.items():
            if feedback_item.timestamp < cutoff_date:
                feedback_to_remove.append(feedback_id)

        for feedback_id in feedback_to_remove:
            del self.feedback_storage[feedback_id]
            removed_count += 1

        # Remove from history
        self.feedback_history = [
            f for f in self.feedback_history
            if f.timestamp >= cutoff_date
        ]

        logger.info("Cleaned up %d old feedback items", removed_count)
        return removed_count


# Global instance for backward compatibility
human_feedback_system = HumanFeedbackSystem()
