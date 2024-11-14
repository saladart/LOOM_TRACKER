# app/main.py
from flask import Blueprint, flash, redirect, render_template, request, jsonify, send_file, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from werkzeug.security import generate_password_hash

from sqlalchemy import extract, func
from .models import TimeEntry, Project, User
from . import db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    if current_user.is_admin:
        projects = Project.query.all()
    else:
        projects = Project.query.filter_by(is_active=True).all()
    current_month_hours = TimeEntry.query\
        .filter(TimeEntry.user_id == current_user.id)\
        .filter(extract('month', TimeEntry.date) == datetime.now().month) \
        .with_entities(func.sum(TimeEntry.hours))\
        .scalar() or 0
        
    return render_template('index.html', 
                        projects=projects,
                        current_month_hours=current_month_hours)

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
    
    query = TimeEntry.query\
        .join(Project)\
        .filter(TimeEntry.date.between(start_date, end_date))
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    if data.get('projects'):
        query = query.filter(Project.id.in_(data['projects']))
    
    entries = query.all()
    
    df = pd.DataFrame([{
        'Date': entry.date,
        'Project': entry.project.name,
        'Hours': entry.hours,
        'User': entry.user.username
    } for entry in entries])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
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
        return redirect(url_for('main.index'))
    
    return render_template('add_project.html')

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

