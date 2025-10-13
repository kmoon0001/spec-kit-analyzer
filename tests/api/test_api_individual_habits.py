import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import crud, schemas, models
from src.auth import AuthService
from unittest.mock import patch, AsyncMock
from datetime import datetime

@pytest.mark.asyncio
async def test_get_personal_habit_profile(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the IndividualHabitTracker
    with patch("src.api.routers.individual_habits.IndividualHabitTracker") as mock_tracker_class:
        mock_tracker_instance = AsyncMock()
        mock_tracker_instance.get_personal_habit_profile.return_value = {"test": "profile"}
        mock_tracker_class.return_value = mock_tracker_instance

        # Get the profile
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/habits/individual/profile", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"test": "profile"}

@pytest.mark.asyncio
async def test_get_habit_timeline(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_timeline_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the IndividualHabitTracker
    with patch("src.api.routers.individual_habits.IndividualHabitTracker") as mock_tracker_class:
        mock_tracker_instance = AsyncMock()
        mock_tracker_instance.get_habit_timeline.return_value = {"test": "timeline"}
        mock_tracker_class.return_value = mock_tracker_instance

        # Get the timeline
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/habits/individual/timeline/habit_1", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"test": "timeline"}

@pytest.mark.asyncio
async def test_get_personal_goals(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_goals_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the crud function
    with patch("src.api.routers.individual_habits.crud.get_user_habit_goals", new_callable=AsyncMock) as mock_get_goals:
        mock_get_goals.return_value = []

        # Get the goals
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/habits/individual/goals", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"user_id": user.id, "goals": [], "total_goals": 0}

@pytest.mark.asyncio
async def test_create_personal_goal(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_create_goal_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the crud function
    with patch("src.api.routers.individual_habits.crud.create_personal_habit_goal", new_callable=AsyncMock) as mock_create_goal:
        mock_create_goal.return_value = models.HabitGoal(id=1, user_id=user.id, title="Test Goal", habit_number=1, target_value=5.0, current_value=0.0, progress=0, status="active", created_at=datetime.utcnow(), updated_at=datetime.utcnow(), target_date=datetime.utcnow())

        # Create a goal
        headers = {"Authorization": f"Bearer {token}"}
        goal_data = {
            "habit_id": "habit_1",
            "goal_type": "reduce_findings",
            "target_value": 5.0,
            "target_date": "2025-03-01T00:00:00Z"
        }
        response = await client.post("/habits/individual/goals", json=goal_data, headers=headers)
        assert response.status_code == 200
        assert "message" in response.json()

@pytest.mark.asyncio
async def test_get_personal_achievements(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_achievements_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the crud function and settings
    with patch("src.api.routers.individual_habits.crud.get_user_achievements", new_callable=AsyncMock) as mock_get_achievements, \
         patch("src.api.routers.individual_habits.get_settings") as mock_get_settings:
        mock_get_achievements.return_value = []
        mock_get_settings.return_value.habits_framework.gamification.enabled = True

        # Get the achievements
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/habits/individual/achievements", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"user_id": user.id, "total_achievements": 0, "total_points": 0, "achievements_by_category": {}, "categories": []}

@pytest.mark.asyncio
async def test_get_personal_statistics(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_stats_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the crud function
    with patch("src.api.routers.individual_habits.crud.get_user_habit_statistics", new_callable=AsyncMock) as mock_get_stats:
        mock_get_stats.return_value = {"test": "stats"}

        # Get the statistics
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/habits/individual/statistics", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"test": "stats"}

@pytest.mark.asyncio
async def test_get_all_habits_info(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_info_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Get the habits info
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/habits/individual/habits-info", headers=headers)
    assert response.status_code == 200
    assert "habits" in response.json()

@pytest.mark.asyncio
async def test_create_progress_snapshot(client: AsyncClient, db_session: AsyncSession):
    # Create a user and log in
    user_create = schemas.UserCreate(username="habit_snapshot_user", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Mock the IndividualHabitTracker and crud function
    with patch("src.api.routers.individual_habits.IndividualHabitTracker") as mock_tracker_class, \
         patch("src.api.routers.individual_habits.crud.create_habit_progress_snapshot", new_callable=AsyncMock) as mock_create_snapshot, \
         patch("src.api.routers.individual_habits.get_settings") as mock_get_settings:
        mock_tracker_instance = AsyncMock()
        mock_tracker_instance.get_personal_habit_profile.return_value = {
            "habit_progression": {"habit_breakdown": {}, "total_findings": 0, "top_focus_areas": []},
            "analysis_period": {"total_reports": 0},
            "personal_insights": {"improvement_trend": {}},
        }
        mock_tracker_class.return_value = mock_tracker_instance
        mock_create_snapshot.return_value = models.HabitProgressSnapshot(id=1, user_id=user.id, snapshot_date=datetime.utcnow().date(), overall_progress_score=0.0)
        mock_get_settings.return_value.habits_framework.privacy.track_progression = True

        # Create a snapshot
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/habits/individual/snapshot", headers=headers)
        assert response.status_code == 200
        assert "message" in response.json()