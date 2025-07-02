from flask import Flask, request, redirect, url_for, session, render_template, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
import base64
import secrets
import os
from datetime import datetime, timedelta
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eve_industry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# EVE SSO Configuration
app.config['EVE_CLIENT_ID'] = os.environ.get('EVE_CLIENT_ID', 'your_client_id_here')
app.config['EVE_CLIENT_SECRET'] = os.environ.get('EVE_CLIENT_SECRET', 'your_client_secret_here')
app.config['EVE_CALLBACK_URL'] = os.environ.get('EVE_CALLBACK_URL', 'http://localhost:5000/sso/callback')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, unique=True, nullable=False)
    character_name = db.Column(db.String(100), nullable=False)
    corporation_id = db.Column(db.Integer, nullable=True)
    corporation_name = db.Column(db.String(100), nullable=True)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

class RequiredJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corporation_id = db.Column(db.Integer, nullable=False)
    type_id = db.Column(db.Integer, nullable=False)  # Item type ID
    type_name = db.Column(db.String(200), nullable=False)
    activity_id = db.Column(db.Integer, nullable=False)  # Industry activity (1=manufacturing, 3=research_te, etc.)
    quantity_required = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    deadline = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)

class IndustryJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, unique=True, nullable=False)  # ESI job ID
    installer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    facility_id = db.Column(db.BigInteger, nullable=False)
    station_id = db.Column(db.BigInteger, nullable=False)
    activity_id = db.Column(db.Integer, nullable=False)
    blueprint_id = db.Column(db.BigInteger, nullable=False)
    blueprint_type_id = db.Column(db.Integer, nullable=False)
    blueprint_location_id = db.Column(db.BigInteger, nullable=False)
    output_location_id = db.Column(db.BigInteger, nullable=False)
    runs = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=True)
    licensed_runs = db.Column(db.Integer, nullable=True)
    probability = db.Column(db.Float, nullable=True)
    product_type_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False)  # active, paused, ready, delivered, cancelled, reverted
    duration = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    pause_date = db.Column(db.DateTime, nullable=True)
    completed_date = db.Column(db.DateTime, nullable=True)
    completed_character_id = db.Column(db.Integer, nullable=True)
    successful_runs = db.Column(db.Integer, nullable=True)
    corporation_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    required_job_id = db.Column(db.Integer, db.ForeignKey('required_job.id'), nullable=False)
    industry_job_id = db.Column(db.Integer, db.ForeignKey('industry_job.id'), nullable=False)
    quantity_assigned = db.Column(db.Integer, nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'character_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'character_id' not in session:
            return redirect(url_for('login'))
        user = User.query.filter_by(character_id=session['character_id']).first()
        if not user or not user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ESI API Helper Functions
def get_esi_headers(access_token=None):
    headers = {
        'User-Agent': 'EVE Industry Tracker v1.0',
        'Content-Type': 'application/json'
    }
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    return headers

def refresh_access_token(user):
    """Refresh the access token for a user"""
    auth_string = f"{app.config['EVE_CLIENT_ID']}:{app.config['EVE_CLIENT_SECRET']}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'login.eveonline.com'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.refresh_token
    }
    
    response = requests.post('https://login.eveonline.com/v2/oauth/token', headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        user.access_token = token_data['access_token']
        user.token_expires = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        db.session.commit()
        return True
    return False

def get_valid_token(user):
    """Get a valid access token for a user, refreshing if necessary"""
    if user.token_expires and user.token_expires <= datetime.utcnow():
        if not refresh_access_token(user):
            return None
    return user.access_token

def fetch_character_industry_jobs(user):
    """Fetch industry jobs for a character from ESI"""
    token = get_valid_token(user)
    if not token:
        return None
    
    url = f'https://esi.evetech.net/latest/characters/{user.character_id}/industry/jobs/'
    headers = get_esi_headers(token)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def fetch_corporation_industry_jobs(user):
    """Fetch industry jobs for a corporation from ESI"""
    if not user.corporation_id:
        return None
        
    token = get_valid_token(user)
    if not token:
        return None
    
    url = f'https://esi.evetech.net/latest/corporations/{user.corporation_id}/industry/jobs/'
    headers = get_esi_headers(token)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_type_info(type_id):
    """Get type information from ESI"""
    url = f'https://esi.evetech.net/latest/universe/types/{type_id}/'
    headers = get_esi_headers()
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# Routes
@app.route('/')
def index():
    if 'character_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login')
def login():
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    scopes = [
        'esi-industry.read_character_jobs.v1',
        'esi-industry.read_corporation_jobs.v1',
        'esi-characters.read_corporation_roles.v1'
    ]
    
    auth_url = (
        f"https://login.eveonline.com/v2/oauth/authorize/"
        f"?response_type=code"
        f"&redirect_uri={app.config['EVE_CALLBACK_URL']}"
        f"&client_id={app.config['EVE_CLIENT_ID']}"
        f"&scope={' '.join(scopes)}"
        f"&state={state}"
    )
    
    return redirect(auth_url)

@app.route('/sso/callback')
def sso_callback():
    if request.args.get('state') != session.get('oauth_state'):
        flash('Invalid OAuth state. Please try again.', 'error')
        return redirect(url_for('index'))
    
    code = request.args.get('code')
    if not code:
        flash('No authorization code received.', 'error')
        return redirect(url_for('index'))
    
    # Exchange code for tokens
    auth_string = f"{app.config['EVE_CLIENT_ID']}:{app.config['EVE_CLIENT_SECRET']}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'login.eveonline.com'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code
    }
    
    response = requests.post('https://login.eveonline.com/v2/oauth/token', headers=headers, data=data)
    
    if response.status_code != 200:
        flash('Failed to get access token.', 'error')
        return redirect(url_for('index'))
    
    token_data = response.json()
    
    # Verify JWT token and get character info
    try:
        import jwt
        payload = jwt.decode(token_data['access_token'], options={"verify_signature": False})
        character_id = int(payload['sub'].split(':')[-1])
        character_name = payload['name']
    except Exception as e:
        flash('Failed to decode access token.', 'error')
        return redirect(url_for('index'))
    
    # Get or create user
    user = User.query.filter_by(character_id=character_id).first()
    if not user:
        user = User(character_id=character_id, character_name=character_name)
        db.session.add(user)
    else:
        user.character_name = character_name
        user.last_login = datetime.utcnow()
    
    user.access_token = token_data['access_token']
    user.refresh_token = token_data['refresh_token']
    user.token_expires = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
    
    # Get character's corporation info
    char_info_url = f'https://esi.evetech.net/latest/characters/{character_id}/'
    char_response = requests.get(char_info_url, headers=get_esi_headers(user.access_token))
    if char_response.status_code == 200:
        char_data = char_response.json()
        user.corporation_id = char_data.get('corporation_id')
        
        # Get corporation name
        if user.corporation_id:
            corp_url = f'https://esi.evetech.net/latest/corporations/{user.corporation_id}/'
            corp_response = requests.get(corp_url, headers=get_esi_headers())
            if corp_response.status_code == 200:
                corp_data = corp_response.json()
                user.corporation_name = corp_data.get('name')
    
    db.session.commit()
    
    session['character_id'] = character_id
    session['character_name'] = character_name
    flash(f'Welcome, {character_name}!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.filter_by(character_id=session['character_id']).first()
    
    # Get required jobs for the corporation
    required_jobs = []
    if user.corporation_id:
        required_jobs = RequiredJob.query.filter_by(
            corporation_id=user.corporation_id,
            is_active=True
        ).order_by(RequiredJob.priority.desc(), RequiredJob.deadline.asc()).all()
    
    # Get recent industry jobs
    recent_jobs = IndustryJob.query.filter_by(
        corporation_id=user.corporation_id
    ).order_by(IndustryJob.updated_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         required_jobs=required_jobs,
                         recent_jobs=recent_jobs)

@app.route('/jobs/required')
@login_required
def required_jobs():
    user = User.query.filter_by(character_id=session['character_id']).first()
    
    if not user.corporation_id:
        flash('You must be in a corporation to view required jobs.', 'warning')
        return redirect(url_for('dashboard'))
    
    jobs = RequiredJob.query.filter_by(
        corporation_id=user.corporation_id,
        is_active=True
    ).order_by(RequiredJob.priority.desc(), RequiredJob.deadline.asc()).all()
    
    return render_template('required_jobs.html', jobs=jobs, user=user)

@app.route('/jobs/industry')
@login_required
def industry_jobs():
    user = User.query.filter_by(character_id=session['character_id']).first()
    
    # Sync jobs from ESI
    sync_industry_jobs(user)
    
    jobs = IndustryJob.query.filter_by(
        corporation_id=user.corporation_id
    ).order_by(IndustryJob.updated_at.desc()).all()
    
    return render_template('industry_jobs.html', jobs=jobs, user=user)

@app.route('/admin')
@admin_required
def admin_panel():
    user = User.query.filter_by(character_id=session['character_id']).first()
    
    # Get statistics
    stats = {
        'total_users': User.query.filter_by(corporation_id=user.corporation_id).count(),
        'active_required_jobs': RequiredJob.query.filter_by(
            corporation_id=user.corporation_id, 
            is_active=True
        ).count(),
        'active_industry_jobs': IndustryJob.query.filter_by(
            corporation_id=user.corporation_id,
            status='active'
        ).count()
    }
    
    return render_template('admin.html', user=user, stats=stats)

@app.route('/admin/jobs/create', methods=['GET', 'POST'])
@admin_required
def create_required_job():
    if request.method == 'POST':
        user = User.query.filter_by(character_id=session['character_id']).first()
        
        job = RequiredJob(
            corporation_id=user.corporation_id,
            type_id=request.form['type_id'],
            type_name=request.form['type_name'],
            activity_id=request.form['activity_id'],
            quantity_required=request.form['quantity_required'],
            priority=request.form['priority'],
            notes=request.form.get('notes'),
            created_by=user.id
        )
        
        if request.form.get('deadline'):
            job.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        
        db.session.add(job)
        db.session.commit()
        
        flash('Required job created successfully!', 'success')
        return redirect(url_for('required_jobs'))
    
    return render_template('create_job.html')

@app.route('/admin/users')
@admin_required
def manage_users():
    user = User.query.filter_by(character_id=session['character_id']).first()
    
    users = User.query.filter_by(corporation_id=user.corporation_id).all()
    return render_template('manage_users.html', users=users, current_user=user)

@app.route('/api/sync-jobs', methods=['POST'])
@login_required
def sync_jobs():
    user = User.query.filter_by(character_id=session['character_id']).first()
    success = sync_industry_jobs(user)
    
    return jsonify({'success': success})

def sync_industry_jobs(user):
    """Sync industry jobs from ESI to database"""
    try:
        # Fetch jobs from ESI
        char_jobs = fetch_character_industry_jobs(user)
        corp_jobs = fetch_corporation_industry_jobs(user) if user.corporation_id else []
        
        all_jobs = []
        if char_jobs:
            all_jobs.extend(char_jobs)
        if corp_jobs:
            all_jobs.extend(corp_jobs)
        
        for job_data in all_jobs:
            # Check if job already exists
            existing_job = IndustryJob.query.filter_by(job_id=job_data['job_id']).first()
            
            if existing_job:
                # Update existing job
                existing_job.status = job_data['status']
                existing_job.updated_at = datetime.utcnow()
                if job_data.get('completed_date'):
                    existing_job.completed_date = datetime.fromisoformat(job_data['completed_date'].replace('Z', '+00:00'))
                if job_data.get('pause_date'):
                    existing_job.pause_date = datetime.fromisoformat(job_data['pause_date'].replace('Z', '+00:00'))
            else:
                # Create new job
                new_job = IndustryJob(
                    job_id=job_data['job_id'],
                    installer_id=user.id,
                    facility_id=job_data['facility_id'],
                    station_id=job_data['station_id'],
                    activity_id=job_data['activity_id'],
                    blueprint_id=job_data['blueprint_id'],
                    blueprint_type_id=job_data['blueprint_type_id'],
                    blueprint_location_id=job_data['blueprint_location_id'],
                    output_location_id=job_data['output_location_id'],
                    runs=job_data['runs'],
                    cost=job_data.get('cost'),
                    licensed_runs=job_data.get('licensed_runs'),
                    probability=job_data.get('probability'),
                    product_type_id=job_data.get('product_type_id'),
                    status=job_data['status'],
                    duration=job_data['duration'],
                    start_date=datetime.fromisoformat(job_data['start_date'].replace('Z', '+00:00')),
                    end_date=datetime.fromisoformat(job_data['end_date'].replace('Z', '+00:00')),
                    corporation_id=user.corporation_id
                )
                
                if job_data.get('completed_date'):
                    new_job.completed_date = datetime.fromisoformat(job_data['completed_date'].replace('Z', '+00:00'))
                if job_data.get('pause_date'):
                    new_job.pause_date = datetime.fromisoformat(job_data['pause_date'].replace('Z', '+00:00'))
                
                db.session.add(new_job)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error syncing jobs: {e}")
        return False

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)