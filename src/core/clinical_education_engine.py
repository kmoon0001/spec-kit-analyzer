"""Clinical Education Engine for Therapy Compliance Analysis.

This module provides a comprehensive clinical education system that delivers
personalized learning content, tracks educational progress, and integrates
with compliance analysis to provide contextual learning opportunities.

Features:
- Personalized learning paths
- Interactive educational content
- Progress tracking and assessment
- Integration with compliance findings
- Evidence-based learning materials
- Competency-based education
- Continuing education credits tracking
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class LearningLevel(Enum):
    """Learning difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContentType(Enum):
    """Types of educational content."""
    ARTICLE = "article"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    CASE_STUDY = "case_study"
    SIMULATION = "simulation"
    WEBINAR = "webinar"


class CompetencyArea(Enum):
    """Clinical competency areas."""
    DOCUMENTATION = "documentation"
    ASSESSMENT = "assessment"
    TREATMENT_PLANNING = "treatment_planning"
    ETHICS = "ethics"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    EVIDENCE_BASED_PRACTICE = "evidence_based_practice"
    COMMUNICATION = "communication"
    SAFETY = "safety"


@dataclass
class LearningObjective:
    """Learning objective definition."""
    objective_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    competency_area: CompetencyArea = CompetencyArea.DOCUMENTATION
    learning_level: LearningLevel = LearningLevel.BEGINNER
    keywords: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 30


@dataclass
class EducationalContent:
    """Educational content item."""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content_type: ContentType = ContentType.ARTICLE
    learning_objective_id: str = ""
    content_url: str = ""
    content_text: str = ""
    duration_minutes: int = 30
    difficulty_level: LearningLevel = LearningLevel.BEGINNER
    tags: List[str] = field(default_factory=list)
    author: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0"


@dataclass
class LearningPath:
    """Personalized learning path."""
    path_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    title: str = ""
    description: str = ""
    competency_focus: CompetencyArea = CompetencyArea.DOCUMENTATION
    learning_level: LearningLevel = LearningLevel.BEGINNER
    objectives: List[LearningObjective] = field(default_factory=list)
    content_items: List[EducationalContent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    estimated_completion_hours: float = 0.0
    progress_percentage: float = 0.0


@dataclass
class LearningProgress:
    """Individual learning progress tracking."""
    progress_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    content_id: str
    learning_path_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    time_spent_minutes: int = 0
    completion_percentage: float = 0.0
    quiz_score: Optional[float] = None
    competency_rating: Optional[float] = None
    feedback: Optional[str] = None


@dataclass
class CompetencyAssessment:
    """Competency assessment result."""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    competency_area: CompetencyArea
    assessment_date: datetime = field(default_factory=datetime.now)
    score: float = 0.0
    level_achieved: LearningLevel = LearningLevel.BEGINNER
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ClinicalEducationEngine:
    """Clinical education engine for therapy compliance analysis.

    Provides personalized learning experiences and tracks educational progress.
    """

    def __init__(self, content_storage_path: str = "education_content"):
        """Initialize the clinical education engine.

        Args:
            content_storage_path: Path to store educational content
        """
        self.content_storage_path = Path(content_storage_path)
        self.content_storage_path.mkdir(exist_ok=True)

        # Learning content storage
        self.learning_objectives: Dict[str, LearningObjective] = {}
        self.educational_content: Dict[str, EducationalContent] = {}
        self.learning_paths: Dict[str, LearningPath] = {}
        self.learning_progress: Dict[str, LearningProgress] = {}
        self.competency_assessments: Dict[str, CompetencyAssessment] = {}

        # User-specific data
        self.user_competencies: Dict[int, Dict[CompetencyArea, float]] = {}
        self.user_learning_history: Dict[int, List[str]] = {}

        # Content recommendations
        self.content_recommendations: Dict[int, List[str]] = {}

        # Initialize with default content
        self._initialize_default_content()

        logger.info("Clinical education engine initialized with %d learning objectives and %d content items",
                   len(self.learning_objectives), len(self.educational_content))

    def _initialize_default_content(self):
        """Initialize with default educational content."""

        # Documentation competency objectives
        doc_objectives = [
            LearningObjective(
                title="Medicare Documentation Requirements",
                description="Understand Medicare documentation requirements for therapy services",
                competency_area=CompetencyArea.DOCUMENTATION,
                learning_level=LearningLevel.INTERMEDIATE,
                keywords=["medicare", "documentation", "requirements", "therapy"],
                estimated_duration_minutes=45
            ),
            LearningObjective(
                title="Functional Outcome Measures",
                description="Learn to document functional outcomes effectively",
                competency_area=CompetencyArea.DOCUMENTATION,
                learning_level=LearningLevel.ADVANCED,
                keywords=["functional", "outcomes", "measures", "assessment"],
                estimated_duration_minutes=60
            ),
            LearningObjective(
                title="Progress Note Writing",
                description="Master the art of writing effective progress notes",
                competency_area=CompetencyArea.DOCUMENTATION,
                learning_level=LearningLevel.BEGINNER,
                keywords=["progress", "notes", "writing", "clinical"],
                estimated_duration_minutes=30
            )
        ]

        # Assessment competency objectives
        assessment_objectives = [
            LearningObjective(
                title="Comprehensive Assessment Techniques",
                description="Learn comprehensive assessment techniques for therapy patients",
                competency_area=CompetencyArea.ASSESSMENT,
                learning_level=LearningLevel.INTERMEDIATE,
                keywords=["assessment", "techniques", "comprehensive", "evaluation"],
                estimated_duration_minutes=90
            ),
            LearningObjective(
                title="Standardized Assessment Tools",
                description="Understand and use standardized assessment tools effectively",
                competency_area=CompetencyArea.ASSESSMENT,
                learning_level=LearningLevel.ADVANCED,
                keywords=["standardized", "tools", "assessment", "validated"],
                estimated_duration_minutes=75
            )
        ]

        # Add all objectives
        for obj in doc_objectives + assessment_objectives:
            self.learning_objectives[obj.objective_id] = obj

        # Create educational content
        self._create_default_content()

    def _create_default_content(self):
        """Create default educational content."""

        # Documentation content
        doc_content = [
            EducationalContent(
                title="Medicare Documentation Essentials",
                content_type=ContentType.ARTICLE,
                learning_objective_id=list(self.learning_objectives.keys())[0],
                content_text="Medicare requires specific documentation elements for therapy services...",
                duration_minutes=45,
                difficulty_level=LearningLevel.INTERMEDIATE,
                tags=["medicare", "documentation", "compliance"],
                author="Clinical Education Team"
            ),
            EducationalContent(
                title="Functional Outcome Documentation",
                content_type=ContentType.INTERACTIVE,
                learning_objective_id=list(self.learning_objectives.keys())[1],
                content_text="Interactive module on documenting functional outcomes...",
                duration_minutes=60,
                difficulty_level=LearningLevel.ADVANCED,
                tags=["functional", "outcomes", "documentation"],
                author="Clinical Education Team"
            ),
            EducationalContent(
                title="Progress Note Writing Quiz",
                content_type=ContentType.QUIZ,
                learning_objective_id=list(self.learning_objectives.keys())[2],
                content_text="Test your knowledge of progress note writing...",
                duration_minutes=30,
                difficulty_level=LearningLevel.BEGINNER,
                tags=["progress", "notes", "quiz"],
                author="Clinical Education Team"
            )
        ]

        # Assessment content
        assessment_content = [
            EducationalContent(
                title="Assessment Techniques Video",
                content_type=ContentType.VIDEO,
                learning_objective_id=list(self.learning_objectives.keys())[3],
                content_text="Video demonstration of assessment techniques...",
                duration_minutes=90,
                difficulty_level=LearningLevel.INTERMEDIATE,
                tags=["assessment", "techniques", "video"],
                author="Clinical Education Team"
            ),
            EducationalContent(
                title="Standardized Tools Case Study",
                content_type=ContentType.CASE_STUDY,
                learning_objective_id=list(self.learning_objectives.keys())[4],
                content_text="Case study on using standardized assessment tools...",
                duration_minutes=75,
                difficulty_level=LearningLevel.ADVANCED,
                tags=["standardized", "tools", "case_study"],
                author="Clinical Education Team"
            )
        ]

        # Add all content
        for content in doc_content + assessment_content:
            self.educational_content[content.content_id] = content

    async def create_personalized_learning_path(
        self,
        user_id: int,
        competency_focus: CompetencyArea,
        learning_level: LearningLevel,
        analysis_findings: Optional[List[Dict[str, Any]]] = None
    ) -> LearningPath:
        """Create a personalized learning path for a user.

        Args:
            user_id: User ID
            competency_focus: Primary competency area to focus on
            learning_level: User's current learning level
            analysis_findings: Recent analysis findings to address

        Returns:
            Personalized learning path
        """
        try:
            # Get user's current competencies
            user_competencies = self.user_competencies.get(user_id, {})
            current_level = user_competencies.get(competency_focus, 0.0)

            # Select appropriate learning objectives
            relevant_objectives = [
                obj for obj in self.learning_objectives.values()
                if obj.competency_area == competency_focus
                and self._is_level_appropriate(obj.learning_level, learning_level, current_level)
            ]

            # If analysis findings provided, prioritize objectives that address them
            if analysis_findings:
                relevant_objectives = self._prioritize_by_findings(relevant_objectives, analysis_findings)

            # Select content for each objective
            selected_content = []
            for objective in relevant_objectives[:5]:  # Limit to 5 objectives
                content_items = [
                    content for content in self.educational_content.values()
                    if content.learning_objective_id == objective.objective_id
                ]
                selected_content.extend(content_items)

            # Create learning path
            learning_path = LearningPath(
                user_id=user_id,
                title=f"{competency_focus.value.title()} Learning Path",
                description=f"Personalized learning path for {competency_focus.value} competency",
                competency_focus=competency_focus,
                learning_level=learning_level,
                objectives=relevant_objectives,
                content_items=selected_content,
                estimated_completion_hours=sum(c.duration_minutes for c in selected_content) / 60.0
            )

            # Store learning path
            self.learning_paths[learning_path.path_id] = learning_path

            logger.info("Created personalized learning path for user %d: %s", user_id, learning_path.path_id)
            return learning_path

        except Exception as e:
            logger.exception("Failed to create learning path for user %d: %s", user_id, e)
            raise

    async def start_learning_session(
        self,
        user_id: int,
        content_id: str,
        learning_path_id: Optional[str] = None
    ) -> LearningProgress:
        """Start a learning session for a user.

        Args:
            user_id: User ID
            content_id: Content ID to learn
            learning_path_id: Optional learning path ID

        Returns:
            Learning progress tracking
        """
        try:
            if content_id not in self.educational_content:
                raise ValueError(f"Content not found: {content_id}")

            # Create progress tracking
            progress = LearningProgress(
                user_id=user_id,
                content_id=content_id,
                learning_path_id=learning_path_id
            )

            # Store progress
            self.learning_progress[progress.progress_id] = progress

            # Update user learning history
            if user_id not in self.user_learning_history:
                self.user_learning_history[user_id] = []
            self.user_learning_history[user_id].append(content_id)

            logger.info("Started learning session for user %d: %s", user_id, content_id)
            return progress

        except Exception as e:
            logger.exception("Failed to start learning session for user %d: %s", user_id, e)
            raise

    async def complete_learning_session(
        self,
        progress_id: str,
        completion_percentage: float = 100.0,
        quiz_score: Optional[float] = None,
        competency_rating: Optional[float] = None,
        feedback: Optional[str] = None
    ) -> LearningProgress:
        """Complete a learning session.

        Args:
            progress_id: Progress ID
            completion_percentage: Completion percentage
            quiz_score: Optional quiz score
            competency_rating: Optional competency rating
            feedback: Optional feedback

        Returns:
            Updated learning progress
        """
        try:
            if progress_id not in self.learning_progress:
                raise ValueError(f"Progress not found: {progress_id}")

            progress = self.learning_progress[progress_id]

            # Update progress
            progress.completed_at = datetime.now()
            progress.completion_percentage = completion_percentage
            progress.quiz_score = quiz_score
            progress.competency_rating = competency_rating
            progress.feedback = feedback

            # Calculate time spent
            if progress.started_at:
                time_spent = (progress.completed_at - progress.started_at).total_seconds() / 60
                progress.time_spent_minutes = int(time_spent)

            # Update user competencies
            await self._update_user_competencies(progress)

            # Update learning path progress if applicable
            if progress.learning_path_id:
                await self._update_learning_path_progress(progress.learning_path_id)

            logger.info("Completed learning session: %s", progress_id)
            return progress

        except Exception as e:
            logger.exception("Failed to complete learning session %s: %s", progress_id, e)
            raise

    async def assess_competency(
        self,
        user_id: int,
        competency_area: CompetencyArea,
        assessment_data: Dict[str, Any]
    ) -> CompetencyAssessment:
        """Assess user competency in a specific area.

        Args:
            user_id: User ID
            competency_area: Competency area to assess
            assessment_data: Assessment data

        Returns:
            Competency assessment result
        """
        try:
            # Calculate competency score based on assessment data
            score = self._calculate_competency_score(assessment_data)

            # Determine level achieved
            level_achieved = self._determine_competency_level(score)

            # Generate strengths and improvement areas
            strengths, improvement_areas = self._analyze_competency_performance(assessment_data)

            # Generate recommendations
            recommendations = self._generate_competency_recommendations(
                competency_area, score, improvement_areas
            )

            # Create assessment
            assessment = CompetencyAssessment(
                user_id=user_id,
                competency_area=competency_area,
                score=score,
                level_achieved=level_achieved,
                strengths=strengths,
                improvement_areas=improvement_areas,
                recommendations=recommendations
            )

            # Store assessment
            self.competency_assessments[assessment.assessment_id] = assessment

            # Update user competencies
            if user_id not in self.user_competencies:
                self.user_competencies[user_id] = {}
            self.user_competencies[user_id][competency_area] = score

            logger.info("Completed competency assessment for user %d in %s: %.2f",
                       user_id, competency_area.value, score)
            return assessment

        except Exception as e:
            logger.exception("Failed to assess competency for user %d: %s", user_id, e)
            raise

    async def get_learning_recommendations(
        self,
        user_id: int,
        analysis_findings: Optional[List[Dict[str, Any]]] = None
    ) -> List[EducationalContent]:
        """Get personalized learning recommendations for a user.

        Args:
            user_id: User ID
            analysis_findings: Recent analysis findings

        Returns:
            List of recommended educational content
        """
        try:
            recommendations = []

            # Get user's current competencies
            user_competencies = self.user_competencies.get(user_id, {})

            # Get user's learning history
            learning_history = self.user_learning_history.get(user_id, [])

            # Find content that addresses competency gaps
            for competency_area, score in user_competencies.items():
                if score < 0.7:  # Competency gap
                    relevant_content = [
                        content for content in self.educational_content.values()
                        if any(obj.competency_area == competency_area
                              for obj in self.learning_objectives.values()
                              if obj.objective_id == content.learning_objective_id)
                        and content.content_id not in learning_history
                    ]
                    recommendations.extend(relevant_content[:2])  # Limit to 2 per competency

            # If analysis findings provided, prioritize content that addresses them
            if analysis_findings:
                findings_recommendations = self._get_content_for_findings(analysis_findings)
                recommendations.extend(findings_recommendations)

            # Remove duplicates and limit results
            unique_recommendations = list({c.content_id: c for c in recommendations}.values())[:10]

            # Store recommendations
            self.content_recommendations[user_id] = [c.content_id for c in unique_recommendations]

            logger.info("Generated %d learning recommendations for user %d",
                       len(unique_recommendations), user_id)
            return unique_recommendations

        except Exception as e:
            logger.exception("Failed to get learning recommendations for user %d: %s", user_id, e)
            return []

    def _is_level_appropriate(
        self,
        content_level: LearningLevel,
        user_level: LearningLevel,
        competency_score: float
    ) -> bool:
        """Check if content level is appropriate for user."""
        level_hierarchy = {
            LearningLevel.BEGINNER: 0,
            LearningLevel.INTERMEDIATE: 1,
            LearningLevel.ADVANCED: 2,
            LearningLevel.EXPERT: 3
        }

        user_level_num = level_hierarchy[user_level]
        content_level_num = level_hierarchy[content_level]

        # Allow content up to one level above user level
        return content_level_num <= user_level_num + 1

    def _prioritize_by_findings(
        self,
        objectives: List[LearningObjective],
        findings: List[Dict[str, Any]]
    ) -> List[LearningObjective]:
        """Prioritize objectives based on analysis findings."""
        prioritized = []

        # Extract keywords from findings
        finding_keywords = set()
        for finding in findings:
            if 'issue_title' in finding:
                finding_keywords.update(finding['issue_title'].lower().split())
            if 'recommendation' in finding:
                finding_keywords.update(finding['recommendation'].lower().split())

        # Score objectives based on keyword matches
        scored_objectives = []
        for obj in objectives:
            score = 0
            for keyword in finding_keywords:
                if keyword in obj.title.lower() or keyword in obj.description.lower():
                    score += 1
                if keyword in obj.keywords:
                    score += 2

            scored_objectives.append((score, obj))

        # Sort by score and return
        scored_objectives.sort(key=lambda x: x[0], reverse=True)
        return [obj for _, obj in scored_objectives]

    def _get_content_for_findings(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[EducationalContent]:
        """Get content that addresses specific findings."""
        relevant_content = []

        for finding in findings:
            finding_keywords = []
            if 'issue_title' in finding:
                finding_keywords.extend(finding['issue_title'].lower().split())

            # Find content that matches finding keywords
            for content in self.educational_content.values():
                content_text = (content.title + " " + content.content_text).lower()
                if any(keyword in content_text for keyword in finding_keywords):
                    relevant_content.append(content)

        return relevant_content[:5]  # Limit to 5 recommendations

    async def _update_user_competencies(self, progress: LearningProgress):
        """Update user competencies based on learning progress."""
        if not progress.competency_rating:
            return

        # Get the competency area for this content
        content = self.educational_content.get(progress.content_id)
        if not content:
            return

        objective = self.learning_objectives.get(content.learning_objective_id)
        if not objective:
            return

        competency_area = objective.competency_area

        # Update competency score
        if progress.user_id not in self.user_competencies:
            self.user_competencies[progress.user_id] = {}

        current_score = self.user_competencies[progress.user_id].get(competency_area, 0.0)

        # Weighted update based on completion and rating
        weight = progress.completion_percentage / 100.0
        new_score = current_score + (progress.competency_rating - current_score) * weight * 0.1

        self.user_competencies[progress.user_id][competency_area] = min(1.0, max(0.0, new_score))

    async def _update_learning_path_progress(self, learning_path_id: str):
        """Update learning path progress."""
        if learning_path_id not in self.learning_paths:
            return

        learning_path = self.learning_paths[learning_path_id]

        # Count completed content
        completed_content = [
            progress for progress in self.learning_progress.values()
            if progress.learning_path_id == learning_path_id
            and progress.completed_at is not None
        ]

        # Calculate progress percentage
        if learning_path.content_items:
            progress_percentage = len(completed_content) / len(learning_path.content_items) * 100
            learning_path.progress_percentage = progress_percentage

    def _calculate_competency_score(self, assessment_data: Dict[str, Any]) -> float:
        """Calculate competency score from assessment data."""
        # Simple scoring based on quiz results and performance
        quiz_score = assessment_data.get('quiz_score', 0.0)
        performance_score = assessment_data.get('performance_score', 0.0)

        # Weighted average
        return (quiz_score * 0.6 + performance_score * 0.4)

    def _determine_competency_level(self, score: float) -> LearningLevel:
        """Determine competency level from score."""
        if score >= 0.9:
            return LearningLevel.EXPERT
        elif score >= 0.7:
            return LearningLevel.ADVANCED
        elif score >= 0.5:
            return LearningLevel.INTERMEDIATE
        else:
            return LearningLevel.BEGINNER

    def _analyze_competency_performance(
        self,
        assessment_data: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Analyze competency performance to identify strengths and improvement areas."""
        strengths = []
        improvement_areas = []

        # Analyze based on assessment data
        if assessment_data.get('quiz_score', 0) >= 0.8:
            strengths.append("Strong theoretical knowledge")
        else:
            improvement_areas.append("Theoretical knowledge")

        if assessment_data.get('performance_score', 0) >= 0.8:
            strengths.append("Good practical application")
        else:
            improvement_areas.append("Practical application skills")

        return strengths, improvement_areas

    def _generate_competency_recommendations(
        self,
        competency_area: CompetencyArea,
        score: float,
        improvement_areas: List[str]
    ) -> List[str]:
        """Generate competency improvement recommendations."""
        recommendations = []

        if score < 0.7:
            recommendations.append(f"Focus on {competency_area.value} competency development")

        for area in improvement_areas:
            if area == "Theoretical knowledge":
                recommendations.append("Complete additional reading and study materials")
            elif area == "Practical application skills":
                recommendations.append("Practice with case studies and simulations")

        return recommendations

    async def get_user_learning_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive learning dashboard for a user.

        Args:
            user_id: User ID

        Returns:
            Learning dashboard data
        """
        try:
            # Get user competencies
            competencies = self.user_competencies.get(user_id, {})

            # Get learning progress
            user_progress = [
                progress for progress in self.learning_progress.values()
                if progress.user_id == user_id
            ]

            # Get learning paths
            user_paths = [
                path for path in self.learning_paths.values()
                if path.user_id == user_id
            ]

            # Get recent assessments
            recent_assessments = [
                assessment for assessment in self.competency_assessments.values()
                if assessment.user_id == user_id
            ]

            # Calculate learning statistics
            total_time_spent = sum(p.time_spent_minutes for p in user_progress)
            completed_sessions = len([p for p in user_progress if p.completed_at])
            average_score = sum(p.quiz_score for p in user_progress if p.quiz_score) / max(1, len([p for p in user_progress if p.quiz_score]))

            dashboard = {
                'user_id': user_id,
                'competencies': {
                    area.value: score for area, score in competencies.items()
                },
                'learning_statistics': {
                    'total_time_spent_hours': total_time_spent / 60.0,
                    'completed_sessions': completed_sessions,
                    'total_sessions': len(user_progress),
                    'average_quiz_score': average_score,
                    'active_learning_paths': len([p for p in user_paths if p.progress_percentage < 100])
                },
                'recent_progress': user_progress[-5:] if user_progress else [],
                'learning_paths': user_paths,
                'recent_assessments': recent_assessments[-3:] if recent_assessments else [],
                'recommendations': self.content_recommendations.get(user_id, [])
            }

            return dashboard

        except Exception as e:
            logger.exception("Failed to get learning dashboard for user %d: %s", user_id, e)
            return {'error': str(e)}

    async def get_education_stats(self) -> Dict[str, Any]:
        """Get overall education system statistics.

        Returns:
            Education system statistics
        """
        return {
            'total_learning_objectives': len(self.learning_objectives),
            'total_educational_content': len(self.educational_content),
            'total_learning_paths': len(self.learning_paths),
            'total_learning_sessions': len(self.learning_progress),
            'total_assessments': len(self.competency_assessments),
            'active_users': len(self.user_competencies),
            'content_by_type': {
                content_type.value: len([c for c in self.educational_content.values() if c.content_type == content_type])
                for content_type in ContentType
            },
            'competency_distribution': {
                competency.value: len([obj for obj in self.learning_objectives.values() if obj.competency_area == competency])
                for competency in CompetencyArea
            }
        }


# Global instance for backward compatibility
clinical_education_engine = ClinicalEducationEngine()
