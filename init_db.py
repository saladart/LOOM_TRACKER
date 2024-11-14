from app import create_app, db
from app.models import User, Project
from werkzeug.security import generate_password_hash

def init_database():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()

        # remove admin user
        User.query.filter_by(username='admin').delete()
        
        # Check if admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            
            # # Add some initial projects
            # projects = [
            #     'MOST ArtGarden',
            #     'ZLIN Sad Svobody',
            #     'Muzeum Langweil'
            # ]
            
            # for project_name in projects:
            #     project = Project(name=project_name)
            #     db.session.add(project)
            
            db.session.commit()
            print("Database initialized with admin user and initial projects")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init_database()