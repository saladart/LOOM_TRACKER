# Time Tracker

A web-based time tracking application for managing projects and tracking work hours. Built with Flask and SQLAlchemy, featuring a modern dark theme interface.

## Features

- **Time Entry Management**
  - Log daily work hours by project
  - Bulk time entry for multiple days
  - Edit/delete past entries
  - Weekly and monthly summaries

- **Project Management**
  - Create and manage projects
  - Set project deadlines
  - Activate/deactivate projects
  - Visual timeline of project assignments

- **User Management**
  - Admin and regular user roles
  - User activation/deactivation
  - Project assignment management
  - Secure authentication

- **Data Export**
  - Export time entries to Excel
  - Filter by date range, projects, and users
  - Aggregation options by project/user

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/loom-timetracker.git

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run the application
python run.py
```

## Default Admin Access
- Username: `admin`
- Password: `admin`

## Configuration
- Database: SQLite (default)
- Server: Waitress WSGI
- Port: 8080 (development) / 80 (production)

## Usage
1. Log in with admin credentials
2. Create projects and users
3. Assign users to projects
4. Users can log their time entries
5. Export data for reporting

## Author
LOOM Studio s.r.o.