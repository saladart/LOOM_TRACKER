# TODO:
# add logging
# Add DB automatic backup

from waitress import serve
from app import create_app
import logging
import sys

# # Configure logging
# logging.basicConfig(
#     filename='app.log',
#     level=logging.,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

app = create_app()

if __name__ == '__main__':
    try:
        # For production on port 80
        # serve(app, host='192.168.3.100', port=80)
        # For development on port 8080
        serve(app, host='localhost', port=8080)
    except PermissionError:
        logging.error("Failed to bind to port 80. Try running as administrator.")
        print("Error: Administrator privileges required to run on port 80")
        print("Please run the script as administrator")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1)