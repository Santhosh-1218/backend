import os
import sys

# Ensure backend root directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel Serverless Function entry point
# Exports 'app' instance for ASGI invocation
