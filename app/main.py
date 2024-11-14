# app/main.py
from flask import Blueprint, flash, redirect, render_template, request, jsonify, send_file, url_for
from flask_login import login_required, current_user
from datetime import datetime
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
    projects = Project.query.all()
    current_month_hours = TimeEntry.query\
        .filter(TimeEntry.user_id == current_user.id)\
        .filter(extract('month', TimeEntry.date) == datetime.now().month)\
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
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {username} created successfully')
        return redirect(url_for('main.add_user'))
        
    return render_template('add_user.html')

@main.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if not current_user.is_admin:
        print('not admin')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        project_name = request.form['project_name']
        if Project.query.filter_by(name=project_name).first():
            flash('Project already exists')
            print('project exists')
            return redirect(url_for('main.add_project'))
        
        new_project = Project(name=project_name)
        db.session.add(new_project)
        db.session.commit()

        flash(f'Project {project_name} created successfully')
        return redirect(url_for('main.index'))
    
    # If the request method is GET, render the add_project.html template
    return render_template('add_project.html')