"""
Growth Journey Widget for Individual Habit Progression.

Displays personal habit mastery, progress trends, achievements,
and personalized recommendations in the dashboard.
"""

import logging
from typing import Any, Dict

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from ..workers.api_worker import APIWorker

logger = logging.getLogger(__name__)


class HabitProgressBar(QWidget):
    """Custom progress bar for habit mastery levels."""
    
    def __init__(self, habit_name: str, percentage: float, mastery_level: str):
        super().__init__()
        self.habit_name = habit_name
        self.percentage = percentage
        self.mastery_level = mastery_level
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress bar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Habit name and mastery level
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.habit_name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        mastery_label = QLabel(self.mastery_level)
        mastery_label.setFont(QFont("Segoe UI", 9))
        
        # Color code mastery level
        if self.mastery_level == "Mastered":
            mastery_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif self.mastery_level == "Proficient":
            mastery_label.setStyleSheet("color: #2980b9; font-weight: bold;")
        elif self.mastery_level == "Developing":
            mastery_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        else:  # Needs Focus
            mastery_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        header_layout.addWidget(mastery_label)
        layout.addLayout(header_layout)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(int(min(self.percentage, 100)))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{self.percentage:.1f}%")
        
        # Style progress bar based on mastery level
        if self.mastery_level == "Mastered":
            progress_bar.setStyleSheet("""
                QProgressBar { border: 2px solid #27ae60; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #27ae60; border-radius: 3px; }
            """)
        elif self.mastery_level == "Proficient":
            progress_bar.setStyleSheet("""
                QProgressBar { border: 2px solid #2980b9; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #2980b9; border-radius: 3px; }
            """)
        elif self.mastery_level == "Developing":
            progress_bar.setStyleSheet("""
                QProgressBar { border: 2px solid #f39c12; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #f39c12; border-radius: 3px; }
            """)
        else:  # Needs Focus
            progress_bar.setStyleSheet("""
                QProgressBar { border: 2px solid #e74c3c; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #e74c3c; border-radius: 3px; }
            """)
        
        layout.addWidget(progress_bar)


class AchievementBadge(QWidget):
    """Widget for displaying achievement badges."""
    
    def __init__(self, achievement: Dict[str, Any]):
        super().__init__()
        self.achievement = achievement
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the achievement badge UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icon
        icon_label = QLabel(self.achievement.get("icon", "🏆"))
        icon_label.setFont(QFont("Segoe UI", 16))
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        
        title_label = QLabel(self.achievement["title"])
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(self.achievement["description"])
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        # Style the badge
        self.setStyleSheet("""
            AchievementBadge {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
            AchievementBadge:hover {
                background-color: #e9ecef;
            }
        """)


class RecommendationCard(QWidget):
    """Widget for displaying habit recommendations."""
    
    def __init__(self, recommendation: Dict[str, Any]):
        super().__init__()
        self.recommendation = recommendation
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the recommendation card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Priority indicator and title
        header_layout = QHBoxLayout()
        
        priority = self.recommendation.get("priority", "medium")
        priority_label = QLabel(priority.upper())
        priority_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        
        if priority == "high":
            priority_label.setStyleSheet("color: #e74c3c; background: #ffebee; padding: 2px 6px; border-radius: 3px;")
        elif priority == "medium":
            priority_label.setStyleSheet("color: #f39c12; background: #fff3cd; padding: 2px 6px; border-radius: 3px;")
        else:
            priority_label.setStyleSheet("color: #2980b9; background: #e3f2fd; padding: 2px 6px; border-radius: 3px;")
        
        header_layout.addWidget(priority_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(self.recommendation["title"])
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.recommendation["description"])
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; margin: 4px 0;")
        layout.addWidget(desc_label)
        
        # Action items
        action_items = self.recommendation.get("action_items", [])
        if action_items:
            actions_label = QLabel("Action Items:")
            actions_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            layout.addWidget(actions_label)
            
            for item in action_items[:3]:  # Show max 3 items
                item_label = QLabel(f"• {item}")
                item_label.setFont(QFont("Segoe UI", 8))
                item_label.setStyleSheet("color: #666; margin-left: 10px;")
                item_label.setWordWrap(True)
                layout.addWidget(item_label)
        
        # Style the card
        self.setStyleSheet("""
            RecommendationCard {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 4px;
            }
            RecommendationCard:hover {
                border-color: #3498db;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)


class GrowthJourneyWidget(QWidget):
    """
    Main widget for displaying individual habit progression and growth journey.
    
    Features:
    - Habit mastery progress bars
    - Achievement badges
    - Personalized recommendations
    - Progress summary metrics
    - Weekly trends visualization
    """
    
    def __init__(self, api_base_url: str, auth_token: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        self.progression_data = None
        self.setup_ui()
        self.setup_refresh_timer()
        self.load_progression_data()
    
    def setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🌟 Your Growth Journey")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.load_progression_data)
        header_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        # Loading indicator
        self.loading_label = QLabel("Loading your growth journey...")
        self.loading_label.setFont(QFont("Segoe UI", 12))
        self.loading_label.setStyleSheet("color: #666; text-align: center; padding: 40px;")
        self.content_layout.addWidget(self.loading_label)
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_progression_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def load_progression_data(self):
        """Load habit progression data from API."""
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Loading...")
        
        # Create API worker
        self.api_worker = APIWorker(
            method="GET",
            url=f"{self.api_base_url}/habits/progression",
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        
        self.api_worker.success.connect(self.on_data_loaded)
        self.api_worker.error.connect(self.on_data_error)
        self.api_worker.start()
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """Handle successful data loading."""
        self.progression_data = data
        self.update_ui()
        
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Refresh")
    
    def on_data_error(self, error: str):
        """Handle data loading error."""
        logger.error(f"Failed to load progression data: {error}")
        
        # Show error message
        self.clear_content()
        error_label = QLabel(f"Failed to load growth journey data: {error}")
        error_label.setStyleSheet("color: #e74c3c; text-align: center; padding: 40px;")
        self.content_layout.addWidget(error_label)
        
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Retry")
    
    def clear_content(self):
        """Clear all content widgets."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_ui(self):
        """Update UI with loaded progression data."""
        if not self.progression_data:
            return
        
        self.clear_content()
        
        # Overall progress summary
        self.add_progress_summary()
        
        # Habit mastery levels
        self.add_habit_mastery_section()
        
        # Recent achievements
        self.add_achievements_section()
        
        # Recommendations
        self.add_recommendations_section()
        
        # Current goals (if any)
        self.add_goals_section()
    
    def add_progress_summary(self):
        """Add overall progress summary section."""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                color: white;
                padding: 16px;
            }
        """)
        
        summary_layout = QGridLayout(summary_frame)
        
        # Overall progress
        overall_progress = self.progression_data.get("overall_progress", {})
        
        progress_label = QLabel(f"{overall_progress.get('percentage', 0):.1f}%")
        progress_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        progress_label.setStyleSheet("color: white;")
        summary_layout.addWidget(progress_label, 0, 0)
        
        status_label = QLabel(f"Status: {overall_progress.get('status', 'Unknown')}")
        status_label.setFont(QFont("Segoe UI", 12))
        status_label.setStyleSheet("color: rgba(255,255,255,0.9);")
        summary_layout.addWidget(status_label, 1, 0)
        
        # Current streak
        streak = self.progression_data.get("current_streak", 0)
        streak_label = QLabel(f"🔥 {streak} day streak")
        streak_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        streak_label.setStyleSheet("color: white;")
        summary_layout.addWidget(streak_label, 0, 1)
        
        # Improvement rate
        improvement_rate = self.progression_data.get("improvement_rate", 0)
        if improvement_rate > 0:
            improvement_text = f"📈 +{improvement_rate:.1f}% improving"
            color = "lightgreen"
        elif improvement_rate < 0:
            improvement_text = f"📉 {improvement_rate:.1f}% declining"
            color = "lightcoral"
        else:
            improvement_text = "📊 Stable performance"
            color = "white"
        
        improvement_label = QLabel(improvement_text)
        improvement_label.setFont(QFont("Segoe UI", 10))
        improvement_label.setStyleSheet(f"color: {color};")
        summary_layout.addWidget(improvement_label, 1, 1)
        
        self.content_layout.addWidget(summary_frame)
    
    def add_habit_mastery_section(self):
        """Add habit mastery progress bars."""
        mastery_frame = QFrame()
        mastery_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        mastery_layout = QVBoxLayout(mastery_frame)
        
        # Section title
        title_label = QLabel("📊 Habit Mastery Levels")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 12px;")
        mastery_layout.addWidget(title_label)
        
        # Habit progress bars
        habit_breakdown = self.progression_data.get("habit_breakdown", {})
        
        for habit_id in sorted(habit_breakdown.keys(), key=lambda x: int(x.split("_")[1])):
            habit_data = habit_breakdown[habit_id]
            
            progress_bar = HabitProgressBar(
                habit_name=f"Habit {habit_data['habit_number']}: {habit_data['habit_name']}",
                percentage=habit_data["percentage"],
                mastery_level=habit_data["mastery_level"]
            )
            
            mastery_layout.addWidget(progress_bar)
        
        self.content_layout.addWidget(mastery_frame)
    
    def add_achievements_section(self):
        """Add recent achievements section."""
        achievements = self.progression_data.get("achievements", [])
        
        if not achievements:
            return
        
        achievements_frame = QFrame()
        achievements_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        achievements_layout = QVBoxLayout(achievements_frame)
        
        # Section title
        title_label = QLabel("🏆 Recent Achievements")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 12px;")
        achievements_layout.addWidget(title_label)
        
        # Achievement badges (show last 3)
        for achievement in achievements[:3]:
            badge = AchievementBadge(achievement)
            achievements_layout.addWidget(badge)
        
        self.content_layout.addWidget(achievements_frame)
    
    def add_recommendations_section(self):
        """Add personalized recommendations section."""
        recommendations = self.progression_data.get("recommendations", [])
        
        if not recommendations:
            return
        
        recommendations_frame = QFrame()
        recommendations_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        recommendations_layout = QVBoxLayout(recommendations_frame)
        
        # Section title
        title_label = QLabel("💡 Personalized Recommendations")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 12px;")
        recommendations_layout.addWidget(title_label)
        
        # Recommendation cards (show top 3)
        for recommendation in recommendations[:3]:
            card = RecommendationCard(recommendation)
            recommendations_layout.addWidget(card)
        
        self.content_layout.addWidget(recommendations_frame)
    
    def add_goals_section(self):
        """Add current goals section."""
        goals = self.progression_data.get("current_goals", [])
        
        if not goals:
            return
        
        goals_frame = QFrame()
        goals_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        goals_layout = QVBoxLayout(goals_frame)
        
        # Section title
        title_label = QLabel("🎯 Current Goals")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 12px;")
        goals_layout.addWidget(title_label)
        
        # Goal progress bars
        for goal in goals:
            goal_layout = QVBoxLayout()
            
            # Goal title
            goal_title = QLabel(goal["title"])
            goal_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            goal_layout.addWidget(goal_title)
            
            # Goal description
            goal_desc = QLabel(goal["description"])
            goal_desc.setFont(QFont("Segoe UI", 9))
            goal_desc.setStyleSheet("color: #666;")
            goal_desc.setWordWrap(True)
            goal_layout.addWidget(goal_desc)
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(goal["progress"])
            progress_bar.setFormat(f"{goal['progress']}%")
            goal_layout.addWidget(progress_bar)
            
            goals_layout.addLayout(goal_layout)
        
        self.content_layout.addWidget(goals_frame)