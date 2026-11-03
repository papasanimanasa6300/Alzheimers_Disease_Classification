"""
Alzheimer's Disease Classification and Cognitive Assessment Platform
Main entry point.
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"Starting Alzheimer's Disease Classification & Cognitive Assessment Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
