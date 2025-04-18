import os
import mimetypes
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

# Initialize MIME types
mimetypes.init()

# List of common code file extensions
CODE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'React JSX',
    '.ts': 'TypeScript',
    '.tsx': 'React TSX',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
    '.scala': 'Scala',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.sql': 'SQL',
    '.r': 'R',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.toml': 'TOML',
    '.dart': 'Dart',
    '.lua': 'Lua'
}

def is_code_file(file_path):
    """
    Determine if a file is a code file based on its extension and content
    """
    if not os.path.isfile(file_path):
        return False
    
    # Check if the file is a binary file
    if is_binary(file_path):
        return False
    
    # Check extension
    _, ext = os.path.splitext(file_path.lower())
    if ext in CODE_EXTENSIONS:
        return True
    
    # Try to determine using pygments
    try:
        get_lexer_for_filename(file_path)
        return True
    except ClassNotFound:
        pass
    
    # Check if it's a text file by MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('text/'):
        return True
        
    return False

def is_binary(file_path, sample_size=8000):
    """
    Check if the file is binary by examining its contents
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        
        # Check if there are null bytes
        if b'\x00' in sample:
            return True
        
        # Check if it's UTF-8 decodable
        try:
            sample.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True
    except:
        return True

def read_file_content(file_path):
    """
    Read and return the content of a file
    """
    if is_binary(file_path):
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def get_file_language(file_path):
    """
    Determine the programming language of the file
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext in CODE_EXTENSIONS:
        return CODE_EXTENSIONS[ext]
    
    try:
        lexer = get_lexer_for_filename(file_path)
        return lexer.name
    except ClassNotFound:
        return "Unknown"

def get_file_size(file_path):
    """
    Get the size of a file in bytes
    """
    return os.path.getsize(file_path) if os.path.isfile(file_path) else 0 