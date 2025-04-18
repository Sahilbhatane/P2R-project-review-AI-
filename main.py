from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import time
import json
import tempfile
import shutil
from werkzeug.utils import secure_filename
from src.code_analyzer.analyzer import CodeAnalyzer
from src.github_handler.github import GitHubRepo
from src.utils.file_utils import is_code_file, read_file_content

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'p2r_uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        flash('No files selected')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('index'))
    
    # Create a project directory with timestamp
    project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"project_{int(time.time())}")
    os.makedirs(project_dir, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(project_dir, filename)
            file.save(file_path)
            uploaded_files.append(file_path)
    
    return analyze_project(project_dir)

@app.route('/github', methods=['POST'])
def github_repo():
    repo_url = request.form.get('repo_url')
    if not repo_url:
        flash('Please enter a GitHub repository URL')
        return redirect(url_for('index'))
    
    try:
        # Create a project directory with timestamp
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"github_{int(time.time())}")
        github_handler = GitHubRepo(repo_url, project_dir)
        github_handler.clone_repo()
        
        return analyze_project(project_dir)
    except Exception as e:
        flash(f'Error cloning repository: {str(e)}')
        return redirect(url_for('index'))

def analyze_project(project_dir):
    analyzer = CodeAnalyzer()
    
    # Collect files
    all_files = []
    for root, _, files in os.walk(project_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            if is_code_file(file_path):
                all_files.append({
                    'path': rel_path,
                    'full_path': file_path
                })
    
    # Analyze each file
    analysis_results = []
    for file_info in all_files:
        file_content = read_file_content(file_info['full_path'])
        analysis = analyzer.analyze_file(file_info['path'], file_content)
        analysis_results.append(analysis)
    
    # Generate project summary
    project_summary = analyzer.generate_project_summary(analysis_results)
    
    # Store results in session or temporary file
    session_id = str(int(time.time()))
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    with open(result_path, 'w') as f:
        json.dump({
            'files': analysis_results,
            'summary': project_summary
        }, f)
    
    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        flash('Analysis results not found')
        return redirect(url_for('index'))
    
    with open(result_path, 'r') as f:
        analysis_data = json.load(f)
    
    return render_template('results.html', 
                          files=analysis_data['files'],
                          summary=analysis_data['summary'])

@app.route('/api/file/<session_id>/<path:file_path>')
def get_file_details(session_id, file_path):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        return jsonify({'error': 'Analysis results not found'}), 404
    
    with open(result_path, 'r') as f:
        analysis_data = json.load(f)
    
    for file_analysis in analysis_data['files']:
        if file_analysis['path'] == file_path:
            return jsonify(file_analysis)
    
    return jsonify({'error': 'File not found in analysis results'}), 404

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100MB.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000) 