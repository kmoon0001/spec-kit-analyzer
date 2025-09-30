# This script is for diagnostic purposes.
# It attempts to import the main FastAPI app to reveal any import errors.
try:
    from src.api.main import app
    print("Import successful. The application should be able to start.")
except Exception as e:
    print(f"An error occurred during import: {e}")
    import traceback
    traceback.print_exc()