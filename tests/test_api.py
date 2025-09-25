import os
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_get_settings():
    response = client.get("/settings")
    assert response.status_code == 200
    settings = response.json()
    assert "quantization" in settings
    assert "performance_profile" in settings
    assert "reviewer_difficulty" in settings

def test_update_settings():
    new_settings = {
        "quantization": "8bit",
        "performance_profile": "low",
        "reviewer_difficulty": "strict"
    }
    response = client.put("/settings", json=new_settings)
    assert response.status_code == 200
    updated_settings = response.json()
    assert updated_settings == new_settings

    # Verify that the settings were actually updated
    response = client.get("/settings")
    assert response.status_code == 200
    settings = response.json()
    assert settings == new_settings

def test_analyze_folder():
    # Create a dummy folder with some files
    os.makedirs("test_folder", exist_ok=True)
    with open("test_folder/test1.txt", "w") as f:
        f.write("This is a test document.")
    with open("test_folder/test2.txt", "w") as f:
        f.write("This is another test document.")

    files = []
    for filename in os.listdir("test_folder"):
        file_path = os.path.join("test_folder", filename)
        if os.path.isfile(file_path):
            files.append(('files', (filename, open(file_path, 'rb'))))

    response = client.post("/analyze_folder", files=files, data={"discipline": "PT", "doc_type": "evaluation"})
    assert response.status_code == 202
    result = response.json()
    assert "task_id" in result
    assert "status" in result
    assert result["status"] == "processing"

    # Clean up the dummy folder
    os.remove("test_folder/test1.txt")
    os.remove("test_folder/test2.txt")
    os.rmdir("test_folder")