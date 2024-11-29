# app/main.py
from flask import Blueprint, flash, redirect, render_template, request, jsonify, send_file, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from werkzeug.security import generate_password_hash

from sqlalchemy import extract, func
from .models import TimeEntry, Project, User, ProjectAssignment
from . import db

main = Blueprint('main', __name__)

# In app/main.py, modify the index route:

@main.route('/')
@login_required
def index():
    if current_user.is_admin:
        projects = Project.query.all()
        users = User.query.all()
    else:
        projects = Project.query.filter_by(is_active=True).all()
        users = None

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Weekly summary
    weekly_entries = db.session.query(
        Project.name,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(TimeEntry)\
    .filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= week_ago,
        TimeEntry.date <= today
    ).group_by(Project.name).all()

    # Monthly summary
    monthly_entries = db.session.query(
        Project.name,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(TimeEntry)\
    .filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= month_ago,
        TimeEntry.date <= today
    ).group_by(Project.name).all()

    current_month_hours = TimeEntry.query \
        .filter(TimeEntry.user_id == current_user.id) \
        .filter(extract('month', TimeEntry.date) == datetime.now().month) \
        .with_entities(func.sum(TimeEntry.hours)) \
        .scalar() or 0
    
    # Filter active assignments
    today = datetime.now().date()
    user_assignments = ProjectAssignment.query\
        .filter_by(user_id=current_user.id)\
        .filter(ProjectAssignment.start_date <= today)\
        .filter(ProjectAssignment.end_date >= today)\
        .all()

    return render_template(
        'index.html',
        projects=projects,
        users=users,
        current_month_hours=current_month_hours,
        user_assignments=user_assignments,
        weekly_summary=weekly_entries,
        monthly_summary=monthly_entries,
        week_ago=week_ago,
        month_ago=month_ago,
        today=today
    )

@main.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    data = request.json
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    for entry in data['entries']:
        new_entry = TimeEntry(
            date=date,
            hours=float(entry['hours']),
            project_id=int(entry['project_id']),
            user_id=current_user.id
        )
        db.session.add(new_entry)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@main.route('/export', methods=['POST'])
@login_required
def export_data():
    data = request.json
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    
    query = TimeEntry.query.join(Project).join(User).filter(
        TimeEntry.date.between(start_date, end_date)
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    if data.get('projects'):
        query = query.filter(Project.id.in_(data['projects']))
    
    if data.get('users'):
        query = query.filter(User.id.in_(data['users']))
    
    entries = query.all()
    
    df = pd.DataFrame([{
        'Date': entry.date.strftime('%Y-%m-%d') if hasattr(entry, 'date') else '',
        'Project': entry.project.name if hasattr(entry.project, 'name') else '',
        'User': entry.user.username if hasattr(entry.user, 'username') else '',
        'Hours': entry.hours
    } for entry in entries])
    
    # Sort by date if 'Date' column exists
    if 'Date' in df.columns:
        df = df.sort_values('Date')
    
    # Aggregate data if requested
    aggregate_by = data.get('aggregate_by')
    if aggregate_by == 'project':
        df = df.groupby(['Project']).agg({'Hours': 'sum'}).reset_index()
    elif aggregate_by == 'user':
        df = df.groupby(['User']).agg({'Hours': 'sum'}).reset_index()
    elif aggregate_by == 'project_user':
        df = df.groupby(['Project', 'User']).agg({'Hours': 'sum'}).reset_index()
    
    # Calculate total hours
    total_hours = df['Hours'].sum()
    
    # Get list of columns and indices
    columns = df.columns.tolist()
    hours_idx = columns.index('Hours')
    meta_idx = hours_idx - 1 if hours_idx > 0 else 0

    empty_row = pd.DataFrame([{col: '' for col in columns}])
    # Create empty rows with the same columns
    summary_row = pd.DataFrame([{col: '' for col in columns}])
    summary_row.iloc[0, meta_idx] = 'Total Hours'
    summary_row.iloc[0, hours_idx] = total_hours

    export_range_row = pd.DataFrame([{col: '' for col in columns}])
    export_range_row.iloc[0, meta_idx] = f'Export Range: {start_date} to {end_date}'

    date_generated_row = pd.DataFrame([{col: '' for col in columns}])
    date_generated_row.iloc[0, meta_idx] = f'Date Generated: {datetime.now().strftime("%Y-%m-%d")}'

    # Concatenate the DataFrames
    df = pd.concat([df, empty_row, summary_row, export_range_row, date_generated_row], ignore_index=True)
    
    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'time_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@main.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.add_user'))
            
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=is_admin,
            is_active=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {username} created successfully')
        return redirect(url_for('main.add_user'))
        
    return render_template('add_user.html')

@main.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        project_name = request.form['project_name']
        deadline_str = request.form['deadline']
        
        if Project.query.filter_by(name=project_name).first():
            flash('Project already exists')
            return redirect(url_for('main.add_project'))
        
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            
        new_project = Project(
            name=project_name,
            deadline=deadline,
            is_active=True
        )
        db.session.add(new_project)
        db.session.commit()

        flash(f'Project {project_name} created successfully')
        return redirect(url_for('main.manage_projects'))
    
    return render_template('add_project.html')

@main.route('/set_project_deadline', methods=['POST'])
@login_required
def set_project_deadline():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()
    project_id = data.get('project_id')
    deadline_str = data.get('deadline')

    if not project_id or not deadline_str:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    project = Project.query.get_or_404(project_id)
    project.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    db.session.commit()

    return jsonify({'status': 'success'})

@main.route('/bulk_entry', methods=['GET', 'POST'])
@login_required
def bulk_entry():
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        project_id = request.form['project_id']
        total_hours = float(request.form['hours'])
        hours_per_day = total_hours / (end_date - start_date).days
        
        current_date = start_date
        while current_date <= end_date:
            new_entry = TimeEntry(
                date=current_date,
                hours=hours_per_day,
                project_id=int(project_id),
                user_id=current_user.id
            )
            db.session.add(new_entry)
            current_date = current_date + timedelta(days=1)
            
        db.session.commit()
        flash('Bulk time entries added successfully')
        return redirect(url_for('main.index'))
        
    projects = Project.query.all()
    return render_template('bulk_entry.html', projects=projects)

@main.route('/manage_users')
@login_required
def manage_users():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@main.route('/activate_user/<int:user_id>')
@login_required
def activate_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been activated')
    return redirect(url_for('main.manage_users'))

@main.route('/deactivate_user/<int:user_id>')
@login_required
def deactivate_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot deactivate the admin user')
        return redirect(url_for('main.manage_users'))
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been deactivated')
    return redirect(url_for('main.manage_users'))

@main.route('/manage_projects')
@login_required
def manage_projects():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    projects = Project.query.all()
    return render_template('manage_projects.html', projects=projects)

@main.route('/activate_project/<int:project_id>')
@login_required
def activate_project(project_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    project = Project.query.get_or_404(project_id)
    project.is_active = True
    db.session.commit()
    flash(f'Project {project.name} has been activated')
    return redirect(url_for('main.manage_projects'))

@main.route('/deactivate_project/<int:project_id>')
@login_required
def deactivate_project(project_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    project = Project.query.get_or_404(project_id)
    project.is_active = False
    db.session.commit()
    flash(f'Project {project.name} has been deactivated')
    return redirect(url_for('main.manage_projects'))

# Assignments
@main.route('/admin/timeline')
@login_required
def admin_timeline():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    projects = Project.query.filter_by(is_active=True).all()
    assignments = ProjectAssignment.query.all()
    users = User.query.filter_by(is_active=True).all()

    # Convert projects to dictionaries
    projects_data = [{
        'id': project.id,
        'name': project.name,
        'deadline': project.deadline.isoformat() if project.deadline else None
    } for project in projects]

    # Convert assignments to dictionaries
    assignments_data = [{
        'id': assignment.id,
        'user_id': assignment.user_id,
        'project_id': assignment.project_id,
        'start_date': assignment.start_date.isoformat(),
        'end_date': assignment.end_date.isoformat()
    } for assignment in assignments]

    # Convert users to dictionaries
    users_data = [{
        'id': user.id,
        'username': user.username
    } for user in users]

    return render_template(
        'admin_timeline.html',
        projects=projects_data,
        assignments=assignments_data,
        users=users_data
    )

@main.route('/admin/assignments', methods=['POST'])
@login_required
def create_assignment():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = int(data['user_id'])
    project_id = int(data['project_id'])
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

    assignment = ProjectAssignment(
        user_id=user_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'assignment': {
            'id': assignment.id,
            'user_id': assignment.user_id,
            'project_id': assignment.project_id,
            'start_date': assignment.start_date.isoformat(),
            'end_date': assignment.end_date.isoformat()
        }
    })

@main.route('/admin/assignments/update', methods=['POST'])
@login_required
def update_assignment():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    assignment = ProjectAssignment.query.get(data['id'])
    if assignment:
        assignment.project_id = data['project_id']  # Add this line
        assignment.start_date = datetime.fromisoformat(data['start_date']).date() + timedelta(days=1)
        assignment.end_date = datetime.fromisoformat(data['end_date']).date() + timedelta(days=1)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Assignment not found'}), 404

@main.route('/admin/assignments/delete', methods=['POST'])
@login_required
def delete_assignment():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()
    assignment_id = data.get('id')
    print(assignment_id)
    if not assignment_id:
        print('No assignment ID provided')
        return jsonify({'status': 'error', 'message': 'No assignment ID provided'}), 400

    assignment = ProjectAssignment.query.get(assignment_id)
    if not assignment:
        print('Assignment not found')
        return jsonify({'status': 'error', 'message': 'Assignment not found'}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'status': 'success'})

@main.route('/toggle_admin', methods=['POST'])
@login_required
def toggle_admin():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    make_admin = data.get('make_admin')

    if user_id is None or make_admin is None:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin' or user.id == current_user.id:
        return jsonify({'status': 'error', 'message': 'Cannot modify admin status'}), 400
        
    user.is_admin = make_admin
    db.session.commit()

    return jsonify({'status': 'success'})

# Table to edit entries

@main.route('/my_entries')
@login_required
def my_entries():
    # Get last 30 days entries
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    entries = TimeEntry.query\
        .filter(TimeEntry.user_id == current_user.id)\
        .filter(TimeEntry.date >= thirty_days_ago)\
        .order_by(TimeEntry.date.desc())\
        .all()
        
    projects = Project.query.filter_by(is_active=True).all()
    return render_template('my_entries.html', entries=entries, projects=projects)

@main.route('/update_entry', methods=['POST'])
@login_required
def update_entry():
    data = request.get_json()
    entry = TimeEntry.query.get_or_404(data['id'])
    
    if entry.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    entry.project_id = data['project_id']
    entry.hours = float(data['hours'])
    db.session.commit()
    return jsonify({'status': 'success'})

@main.route('/delete_entry', methods=['POST'])
@login_required
def delete_entry():
    data = request.get_json()
    entry = TimeEntry.query.get_or_404(data['id'])
    
    if entry.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'status': 'success'})