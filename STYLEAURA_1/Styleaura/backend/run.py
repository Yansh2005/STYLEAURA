import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Run without debug/reloader to avoid Windows WinError 10038
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
