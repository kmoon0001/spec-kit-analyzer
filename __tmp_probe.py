from datetime import UTC, datetime
from fastapi.testclient import TestClient

from src.api.main import app
from src.auth import get_current_active_user
from src.database import schemas


def override_get_current_active_user():
    return schemas.User(
        id=1,
        username="test",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(UTC),
    )


app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app)
files = {"file": ("invalid.txt", b"data", "text/plain")}
data = {"discipline": "pt", "analysis_mode": "rubric", "strictness": "ultra"}
resp = client.post("/analysis/analyze", files=files, data=data)
print(resp.status_code)
print(resp.json())
app.dependency_overrides = {}
