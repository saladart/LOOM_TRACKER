# TODO:
# add logging
# Add DB automatic backup

from waitress import serve
from app import create_app
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = create_app()

if __name__ == '__main__':
    try:
        # For production on port 80
        serve(app, host='0.0.0.0', port=80)
    except PermissionError:
        logging.error("Failed to bind to port 80. Try running as administrator.")
        print("Error: Administrator privileges required to run on port 80")
        print("Please run the script as administrator")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1)