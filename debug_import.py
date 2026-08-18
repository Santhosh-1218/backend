import sys
import os

with open("debug_log.txt", "w") as f:
    f.write("Starting debug import...\n")
    try:
        from app.main import app
        f.write("Successfully imported app!\n")
    except Exception as e:
        import traceback
        f.write(f"Error: {e}\n")
        f.write(traceback.format_exc())
