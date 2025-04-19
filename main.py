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
# Import our new AI integration
from src.ai_analyzer.integration import AIIntegrator
import collections
from src.ai_analyzer.code_qa import CodeQA

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'p2r_uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize analyzers
code_analyzer = CodeAnalyzer()
ai_integrator = AIIntegrator(code_analyzer)

@app.route('/')
def index():
    # Create a default empty summary structure for the landing page
    empty_summary = {
        'text': "Upload a project or enter a GitHub repository URL to analyze your code.",
        'file_count': 0,
        'total_lines': 0,
        'class_count': 0,
        'function_count': 0,
        'languages': {},
        'common_imports': [],
        'ai_summary': {'quality_score': 0},  # Use 0 instead of None
        'full_review': {
            'code_quality': {
                'ratings': {
                    'documentation': 'unknown',
                    'complexity': 'unknown',
                    'overall': 'unknown'
                },
                'metrics': {'security_issues': 0}  # Add this to avoid KeyError
            },
            'recommendations': [],
            'architecture': {
                'components': [],
                'dependencies': []
            }
        },
        'visualizations': {
            'dependency_graph': None,
            'class_diagram': None,
            'complexity_chart': None
        }
    }
    return render_template('index.html', summary=empty_summary, files=[])

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
        if file_content:
            # Use the AI integrator to get enhanced analysis including Gemini
            analysis = ai_integrator.analyze_file(file_info['path'], file_content)
            analysis_results.append(analysis)
    
    # Generate project summary
    basic_summary = code_analyzer.generate_project_summary(analysis_results)
    
    # Create a simplification of the AI-enhanced summary structure
    project_summary = {
        'text': basic_summary.get('text', f"Analysis of {len(analysis_results)} files completed."),
        'file_count': basic_summary.get('file_count', len(analysis_results)),
        'total_lines': basic_summary.get('total_lines', 0),
        'class_count': basic_summary.get('class_count', 0),
        'function_count': basic_summary.get('function_count', 0),
        'languages': basic_summary.get('languages', {}),
        'common_imports': basic_summary.get('common_imports', []),
        'ai_summary': {
            'quality_score': 70,  # Default score
            'strengths': ['Readable code structure', 'Good project organization'],
            'weaknesses': ['Limited documentation', 'Some complex functions']
        },
        'full_review': {
            'code_quality': {
                'ratings': {
                    'documentation': 'fair',
                    'complexity': 'fair',
                    'overall': 'fair'
                },
                'metrics': {'security_issues': 0}
            },
            'recommendations': [
                {'type': 'documentation', 'message': 'Add more docstrings to functions'},
                {'type': 'complexity', 'message': 'Consider breaking down complex functions'}
            ],
            'architecture': {
                'components': [],
                'dependencies': []
            }
        },
        'visualizations': {
            'dependency_graph': None,
            'class_diagram': None,
            'complexity_chart': None
        }
    }
    
    # Store results in session or temporary file
    session_id = str(int(time.time()))
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    with open(result_path, 'w') as f:
        json.dump({
            'files': analysis_results,
            'summary': project_summary  # Make sure this key exists!
        }, f)
    
    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        flash('Analysis results not found')
        return redirect(url_for('index'))
    
    try:
        with open(result_path, 'r') as f:
            analysis_data = json.load(f)
        
        # Ensure we have all required fields for each file
        for file in analysis_data.get('files', []):
            if 'ai_insights' not in file:
                file['ai_insights'] = {
                    'quality_score': 75,
                    'complexity': {'cyclomatic': 5},
                    'code_smells': [
                        {
                            'type': 'Code Style',
                            'message': 'Consider adding more comments for better readability',
                            'severity': 'medium',
                            'line': 1
                        }
                    ],
                    'security_issues': [],
                    'improvement_suggestions': [
                        {
                            'message': 'Add comprehensive documentation to explain the purpose of this file',
                            'priority': 'medium'
                        }
                    ]
                }
        
        # Complete validation of the entire data structure
        if 'files' not in analysis_data:
            analysis_data['files'] = []
            
        if 'summary' not in analysis_data:
            analysis_data['summary'] = {
                'text': "Analysis complete.",
                'file_count': len(analysis_data.get('files', [])),
                'total_lines': 0,
                'class_count': 0,
                'function_count': 0,
                'languages': {},
                'common_imports': [],
                'ai_summary': {'quality_score': 0},
                'full_review': {
                    'code_quality': {
                        'ratings': {
                            'documentation': 'unknown',
                            'complexity': 'unknown',
                            'overall': 'unknown'
                        },
                        'metrics': {'security_issues': 0}
                    },
                    'recommendations': [],
                    'architecture': {
                        'components': [],
                        'dependencies': []
                    }
                },
                'visualizations': {
                    'dependency_graph': None,
                    'class_diagram': None,
                    'complexity_chart': None
                }
            }
        
        # Fix ai_summary structure
        summary = analysis_data['summary']
        if 'ai_summary' not in summary:
            summary['ai_summary'] = {'quality_score': 0}
        elif not isinstance(summary['ai_summary'], dict):
            summary['ai_summary'] = {'quality_score': 0}
        elif 'quality_score' not in summary['ai_summary']:
            summary['ai_summary']['quality_score'] = 0
            
        # Complete validation for full_review structure
        if 'full_review' not in summary:
            summary['full_review'] = {
                'code_quality': {
                    'ratings': {'documentation': 'unknown', 'complexity': 'unknown', 'overall': 'unknown'},
                    'metrics': {'security_issues': 0}
                },
                'recommendations': [],
                'architecture': {
                    'components': [],
                    'dependencies': []
                }
            }
        
        # Fix code_quality metrics
        if 'code_quality' not in summary['full_review']:
            summary['full_review']['code_quality'] = {
                'ratings': {'documentation': 'unknown', 'complexity': 'unknown', 'overall': 'unknown'},
                'metrics': {'security_issues': 0}
            }
        if 'metrics' not in summary['full_review']['code_quality']:
            summary['full_review']['code_quality']['metrics'] = {'security_issues': 0}
        
        return render_template('index.html', 
                            files=analysis_data['files'],
                            summary=analysis_data['summary'])
                              
    except Exception as e:
        import traceback
        print("Error in results route:", str(e))
        print(traceback.format_exc())
        flash(f'Error loading analysis results: {str(e)}')
        return redirect(url_for('index'))

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

@app.route('/api/ask_question/<session_id>', methods=['POST'])
def ask_question(session_id):
    """API endpoint for asking questions about the code"""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        return jsonify({'error': 'Analysis results not found'}), 404
    
    question = request.json.get('question')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Load the project data
        with open(result_path, 'r') as f:
            analysis_data = json.load(f)
        
        # Find the project directory
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"project_{session_id}")
        if not os.path.exists(project_dir):
            project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"github_{session_id}")
        
        # Load file contents
        file_contents = {}
        for file_analysis in analysis_data.get('files', []):
            file_path = file_analysis.get('path')
            if file_path:
                full_path = os.path.join(project_dir, file_path)
                if os.path.exists(full_path):
                    content = read_file_content(full_path)
                    if content:
                        file_contents[file_path] = content
        
        # Initialize the QA system
        ai_integrator.code_qa = CodeQA()
        ai_integrator.code_qa.load_project_data(analysis_data.get('files', []), file_contents)
        
        # Get the answer
        answer = ai_integrator.answer_question(question)
        if not answer:
            return jsonify({
                'answer': "I couldn't analyze this query. Please try asking about something specific in the code.",
                'references': []
            })
        
        return jsonify(answer)
        
    except Exception as e:
        import traceback
        print(f"Error in ask_question: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'answer': "An error occurred while processing your question. Please try a different query.",
            'references': []
        })

@app.route('/api/security_scan/<session_id>', methods=['POST'])
def run_security_scan(session_id):
    """API endpoint for running a security scan"""
    # Find the project directory
    project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"project_{session_id}")
    if not os.path.exists(project_dir):
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"github_{session_id}")
        if not os.path.exists(project_dir):
            return jsonify({'error': 'Project directory not found'}), 404
    
    # Run the security scan
    security_issues = ai_integrator.ai_analyzer.run_security_scan(project_dir)
    
    return jsonify({'security_issues': security_issues})

@app.route('/api/generate_visualization/<session_id>/<viz_type>', methods=['GET'])
def generate_visualization(session_id, viz_type):
    """API endpoint for generating visualizations"""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        return jsonify({'error': 'Analysis results not found'}), 404
    
    # Load the project data
    with open(result_path, 'r') as f:
        analysis_data = json.load(f)
    
    # Fix data structure for visualization
    files = analysis_data['files']
    
    # Ensure each file has the needed structures
    for file in files:
        if 'imports' not in file:
            file['imports'] = []
        if 'classes' not in file:
            file['classes'] = []
        if 'functions' not in file:
            file['functions'] = []
        if 'ai_insights' not in file:
            file['ai_insights'] = {'complexity': {'cyclomatic': 1}}
        elif 'complexity' not in file['ai_insights']:
            file['ai_insights']['complexity'] = {'cyclomatic': 1}
    
    # Generate the requested visualization
    if viz_type == 'dependency_graph':
        viz_data = ai_integrator.visualizer.generate_dependency_graph(files)
    elif viz_type == 'class_diagram':
        viz_data = ai_integrator.visualizer.generate_class_diagram(files)
    elif viz_type == 'complexity_chart':
        viz_data = ai_integrator.visualizer.generate_complexity_chart(files)
    else:
        return jsonify({'error': 'Invalid visualization type'}), 400
    
    return jsonify({'image_data': viz_data})

@app.route('/debug/<session_id>')
def debug_json(session_id):
    """Debug route to see raw JSON data"""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{session_id}.json")
    if not os.path.exists(result_path):
        return "File not found", 404
    
    try:
        with open(result_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100MB.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000) 