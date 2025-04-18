import os
import re
import ast
import importlib
import collections
from ..utils.file_utils import get_file_language, get_file_size

# Custom AST visitor to add parent references
class ParentNodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.parent_map = {}
        
    def visit(self, node):
        for child in ast.iter_child_nodes(node):
            self.parent_map[child] = node
            self.visit(child)
        return self.parent_map

class CodeAnalyzer:
    def __init__(self):
        """Initialize the code analyzer"""
        self.language_analyzers = {
            'Python': self._analyze_python,
            'JavaScript': self._analyze_javascript,
            'TypeScript': self._analyze_javascript,  # Reuse JS analyzer
            'Java': self._analyze_java,
            'C#': self._analyze_csharp,
            'C++': self._analyze_cpp,
            'C': self._analyze_c,
            'Go': self._analyze_go,
            'Ruby': self._analyze_ruby,
        }
        
        # Common patterns across languages
        self.patterns = {
            'import': re.compile(r'^\s*(import|from|require|using|include|#include)\s+[^\s;]+', re.MULTILINE),
            'class': re.compile(r'^\s*(class|interface|struct)\s+(\w+)', re.MULTILINE),
            'function': re.compile(r'^\s*(def|function|func|fn|sub|procedure|method|var\s+\w+\s*=\s*function|const\s+\w+\s*=\s*function|\w+\s*:\s*function|\w+\s*=\s*\([^\)]*\)\s*=>)\s*(\w+|\(\s*\))', re.MULTILINE),
            'comment': re.compile(r'^\s*(#|//|/\*|\*|\'\'\'|""").*$', re.MULTILINE),
        }
    
    def analyze_file(self, file_path, content):
        """
        Analyze a file's content and extract important information
        Returns a structured analysis of the file
        """
        if not content:
            return {
                'path': file_path,
                'language': 'Unknown',
                'size': 0,
                'summary': 'Empty or binary file',
                'elements': []
            }
        
        language = get_file_language(file_path)
        file_size = len(content.encode('utf-8'))
        
        # Get the file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # Call the specific language analyzer if available
        if language in self.language_analyzers:
            analysis = self.language_analyzers[language](content, file_path)
        else:
            # Generic analyzer for unsupported languages
            analysis = self._analyze_generic(content, file_path)
        
        # Calculate code metrics
        line_count = len(content.splitlines())
        comment_matches = self.patterns['comment'].findall(content)
        comment_count = len(comment_matches)
        
        # Add basic file info
        analysis.update({
            'path': file_path,
            'language': language,
            'size': file_size,
            'line_count': line_count,
            'comment_count': comment_count,
            'comment_ratio': round(comment_count / line_count, 2) if line_count > 0 else 0
        })
        
        # Generate a summary based on the analysis
        analysis['summary'] = self._generate_file_summary(analysis)
        
        return analysis
    
    def _analyze_generic(self, content, file_path):
        """Generic analyzer for unsupported languages"""
        # Extract imports
        imports = self.patterns['import'].findall(content)
        imports = [imp.strip() for imp in imports]
        
        # Extract classes
        classes = self.patterns['class'].findall(content)
        class_names = [cls[1] for cls in classes] if classes else []
        
        # Extract functions
        functions = self.patterns['function'].findall(content)
        function_names = [func[1] for func in functions] if functions else []
        
        # Extract potential variables (simple heuristic)
        variable_pattern = re.compile(r'^\s*(\w+)\s*=\s*[^=]', re.MULTILINE)
        variables = variable_pattern.findall(content)
        
        # Create elements list
        elements = []
        
        # Add imports
        for imp in imports:
            elements.append({
                'type': 'import',
                'name': imp,
                'line': self._find_line_number(content, imp)
            })
        
        # Add classes
        for i, cls in enumerate(classes):
            elements.append({
                'type': 'class',
                'name': cls[1],
                'line': self._find_line_number(content, f"{cls[0]} {cls[1]}")
            })
        
        # Add functions
        for i, func in enumerate(functions):
            elements.append({
                'type': 'function',
                'name': func[1],
                'line': self._find_line_number(content, func[0] + ' ' + func[1])
            })
        
        # Add top level variables (limit to 10)
        for var in variables[:10]:
            line = self._find_line_number(content, var + ' =')
            if line > 0:  # Only include if we found a line
                elements.append({
                    'type': 'variable',
                    'name': var,
                    'line': line
                })
        
        # Sort elements by line number
        elements.sort(key=lambda x: x.get('line', 0))
        
        return {
            'imports': imports,
            'classes': class_names,
            'functions': function_names,
            'elements': elements
        }
    
    def _analyze_python(self, content, file_path):
        """Python-specific analyzer using AST"""
        elements = []
        imports = []
        classes = []
        functions = []
        variables = []
        
        try:
            # Parse the Python code
            tree = ast.parse(content)
            
            # Create parent map
            visitor = ParentNodeVisitor()
            parent_map = visitor.visit(tree)
            
            # Process each node in the AST
            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                        elements.append({
                            'type': 'import',
                            'name': name.name,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ''
                    for name in node.names:
                        import_str = f"from {module} import {name.name}"
                        imports.append(import_str)
                        elements.append({
                            'type': 'import',
                            'name': import_str,
                            'line': node.lineno
                        })
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    
                    # Get base classes
                    bases = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                    
                    # Get class methods
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)
                    
                    elements.append({
                        'type': 'class',
                        'name': node.name,
                        'bases': bases,
                        'methods': methods,
                        'line': node.lineno
                    })
                
                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    # Check if this function is inside a class
                    parent = parent_map.get(node)
                    is_method = parent and isinstance(parent, ast.ClassDef)
                    
                    if not is_method:
                        functions.append(node.name)
                        
                        # Get parameters
                        params = []
                        for arg in node.args.args:
                            params.append(arg.arg)
                        
                        elements.append({
                            'type': 'function',
                            'name': node.name,
                            'params': params,
                            'line': node.lineno
                        })
                
                # Extract top-level variables
                elif isinstance(node, ast.Assign):
                    parent = parent_map.get(node)
                    is_module_level = parent and isinstance(parent, ast.Module)
                    
                    if is_module_level:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                variables.append(target.id)
                                elements.append({
                                    'type': 'variable',
                                    'name': target.id,
                                    'line': node.lineno
                                })
        except SyntaxError:
            # Fall back to regex for files with syntax errors
            return self._analyze_generic(content, file_path)
        except Exception as e:
            print(f"Error analyzing Python file {file_path}: {str(e)}")
            return self._analyze_generic(content, file_path)
        
        # Sort elements by line number
        elements.sort(key=lambda x: x.get('line', 0))
        
        return {
            'imports': imports,
            'classes': classes,
            'functions': functions,
            'variables': variables,
            'elements': elements
        }
    
    def _analyze_javascript(self, content, file_path):
        """JavaScript/TypeScript specific analyzer"""
        imports = []
        classes = []
        functions = []
        
        # Import patterns (ES6, CommonJS)
        import_patterns = [
            re.compile(r'import\s+(?:{[^}]+}|\w+|\*\s+as\s+\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
            re.compile(r'import\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
            re.compile(r'const|let|var\s+\w+\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', re.MULTILINE)
        ]
        
        for pattern in import_patterns:
            for match in pattern.finditer(content):
                if match and match.group(1):
                    imports.append(match.group(1))
        
        # Class pattern (ES6 classes)
        class_pattern = re.compile(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', re.MULTILINE)
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            parent_class = match.group(2) if match.group(2) else None
            classes.append(class_name)
            
            elements_entry = {
                'type': 'class',
                'name': class_name,
                'line': self._find_line_number(content, f"class {class_name}")
            }
            
            if parent_class:
                elements_entry['extends'] = parent_class
        
        # Function patterns (various JS function syntaxes)
        function_patterns = [
            re.compile(r'function\s+(\w+)\s*\([^)]*\)', re.MULTILINE),  # Standard function
            re.compile(r'const|let|var\s+(\w+)\s*=\s*function\s*\([^)]*\)', re.MULTILINE),  # Function expression
            re.compile(r'const|let|var\s+(\w+)\s*=\s*\([^)]*\)\s*=>', re.MULTILINE),  # Arrow function
            re.compile(r'(\w+)\s*:\s*function\s*\([^)]*\)', re.MULTILINE)  # Object method
        ]
        
        for pattern in function_patterns:
            for match in pattern.finditer(content):
                if match and match.group(1):
                    func_name = match.group(1)
                    functions.append(func_name)
        
        # Extract elements
        elements = []
        
        # Add imports to elements
        for imp in imports:
            elements.append({
                'type': 'import',
                'name': imp,
                'line': self._find_line_number(content, imp)
            })
        
        # Process classes and functions
        for cls in classes:
            elements.append({
                'type': 'class',
                'name': cls,
                'line': self._find_line_number(content, f"class {cls}")
            })
        
        for func in functions:
            elements.append({
                'type': 'function',
                'name': func,
                'line': self._find_line_number(content, func)
            })
        
        # Extract React components (functional and class-based)
        react_component_pattern = re.compile(r'(?:export\s+(?:default\s+)?)?(?:const|class)\s+(\w+)(?:\s+extends\s+React\.Component|\s+extends\s+Component|\s*=\s*\([^)]*\)\s*=>\s*\{)', re.MULTILINE)
        
        for match in react_component_pattern.finditer(content):
            if match and match.group(1):
                component_name = match.group(1)
                if component_name not in classes and component_name not in functions:
                    elements.append({
                        'type': 'component',
                        'name': component_name,
                        'line': self._find_line_number(content, component_name)
                    })
        
        # Sort elements by line number
        elements.sort(key=lambda x: x.get('line', 0))
        
        return {
            'imports': imports,
            'classes': classes,
            'functions': functions,
            'elements': elements
        }
    
    def _analyze_java(self, content, file_path):
        """Java-specific analyzer"""
        # Simplified Java analysis
        package_pattern = re.compile(r'package\s+([\w.]+);')
        import_pattern = re.compile(r'import\s+([\w.]+);')
        class_pattern = re.compile(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?')
        method_pattern = re.compile(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:<[^>]+>\s*)?(?:[\w.]+)\s+(\w+)\s*\([^)]*\)')
        
        package = None
        package_match = package_pattern.search(content)
        if package_match:
            package = package_match.group(1)
        
        imports = []
        for match in import_pattern.finditer(content):
            imports.append(match.group(1))
        
        classes = []
        for match in class_pattern.finditer(content):
            classes.append({
                'name': match.group(1),
                'extends': match.group(2) if match.group(2) else None,
                'implements': match.group(3).split(',') if match.group(3) else []
            })
        
        methods = []
        for match in method_pattern.finditer(content):
            methods.append(match.group(1))
        
        # Extract elements
        elements = []
        
        if package:
            elements.append({
                'type': 'package',
                'name': package,
                'line': self._find_line_number(content, f"package {package}")
            })
        
        for imp in imports:
            elements.append({
                'type': 'import',
                'name': imp,
                'line': self._find_line_number(content, f"import {imp}")
            })
        
        for cls in classes:
            elements.append({
                'type': 'class',
                'name': cls['name'],
                'extends': cls['extends'],
                'implements': cls['implements'],
                'line': self._find_line_number(content, f"class {cls['name']}")
            })
        
        for method in methods:
            elements.append({
                'type': 'method',
                'name': method,
                'line': self._find_line_number(content, method)
            })
        
        # Sort elements by line number
        elements.sort(key=lambda x: x.get('line', 0))
        
        class_names = [cls['name'] for cls in classes]
        
        return {
            'package': package,
            'imports': imports,
            'classes': class_names,
            'methods': methods,
            'elements': elements
        }
    
    def _analyze_csharp(self, content, file_path):
        """C# specific analyzer"""
        # Similar to Java but with C# syntax
        return self._analyze_generic(content, file_path)
    
    def _analyze_cpp(self, content, file_path):
        """C++ specific analyzer"""
        return self._analyze_generic(content, file_path)
    
    def _analyze_c(self, content, file_path):
        """C specific analyzer"""
        return self._analyze_generic(content, file_path)
    
    def _analyze_go(self, content, file_path):
        """Go specific analyzer"""
        return self._analyze_generic(content, file_path)
    
    def _analyze_ruby(self, content, file_path):
        """Ruby specific analyzer"""
        return self._analyze_generic(content, file_path)
    
    def _find_line_number(self, content, pattern_text):
        """Find the line number where a pattern first appears"""
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if pattern_text in line:
                return i + 1
        return 0
    
    def _generate_file_summary(self, analysis):
        """Generate a human-readable summary of the file"""
        language = analysis.get('language', 'Unknown')
        element_count = len(analysis.get('elements', []))
        
        # Count element types
        element_types = collections.Counter()
        for elem in analysis.get('elements', []):
            element_types[elem.get('type', 'unknown')] += 1
        
        # Create a summary based on what we found
        summary_parts = []
        
        if language != 'Unknown':
            summary_parts.append(f"{language} file")
        
        if element_count == 0:
            summary_parts.append("with no significant code elements")
        else:
            elements_desc = []
            
            if element_types['import'] > 0:
                elements_desc.append(f"{element_types['import']} imports")
            
            if element_types['class'] > 0:
                elements_desc.append(f"{element_types['class']} classes")
            
            if element_types['function'] > 0:
                elements_desc.append(f"{element_types['function']} functions")
            
            if element_types['method'] > 0:
                elements_desc.append(f"{element_types['method']} methods")
            
            if element_types['component'] > 0:
                elements_desc.append(f"{element_types['component']} components")
            
            if elements_desc:
                summary_parts.append("containing " + ", ".join(elements_desc))
        
        # Add line count
        line_count = analysis.get('line_count', 0)
        if line_count > 0:
            summary_parts.append(f"with {line_count} lines")
        
        # Add comment ratio info
        comment_ratio = analysis.get('comment_ratio', 0)
        if comment_ratio > 0.2:
            summary_parts.append(f"well-documented ({int(comment_ratio * 100)}% comments)")
        elif comment_ratio > 0:
            summary_parts.append(f"with some documentation ({int(comment_ratio * 100)}% comments)")
        
        return " ".join(summary_parts)
    
    def generate_project_summary(self, file_analyses):
        """
        Generate a comprehensive summary of the entire project
        """
        # Count languages
        languages = collections.Counter()
        file_count = len(file_analyses)
        total_lines = 0
        total_elements = 0
        
        # Collect all classes and functions across files
        all_classes = []
        all_functions = []
        all_imports = []
        
        for analysis in file_analyses:
            language = analysis.get('language', 'Unknown')
            languages[language] += 1
            total_lines += analysis.get('line_count', 0)
            total_elements += len(analysis.get('elements', []))
            
            # Collect classes and functions
            all_classes.extend(analysis.get('classes', []))
            all_functions.extend(analysis.get('functions', []))
            all_imports.extend(analysis.get('imports', []))
        
        # Get most common elements
        most_common_imports = collections.Counter(all_imports).most_common(10)
        
        # Determine the main languages
        main_languages = languages.most_common(3)
        main_languages_text = ", ".join([f"{lang} ({count})" for lang, count in main_languages])
        
        # Generate the summary
        summary = {
            'file_count': file_count,
            'total_lines': total_lines,
            'languages': dict(languages),
            'main_languages': main_languages_text,
            'class_count': len(all_classes),
            'function_count': len(all_functions),
            'common_imports': most_common_imports,
            'total_elements': total_elements,
        }
        
        # Add textual summary
        text_summary = f"Project with {file_count} files ({total_lines} lines of code) "
        text_summary += f"primarily written in {main_languages_text}. "
        text_summary += f"Contains {len(all_classes)} classes and {len(all_functions)} functions. "
        
        # Add something about the project complexity
        if total_elements > 1000:
            text_summary += "This appears to be a large, complex project."
        elif total_elements > 500:
            text_summary += "This is a medium-sized project with moderate complexity."
        elif total_elements > 100:
            text_summary += "This is a small to medium-sized project."
        else:
            text_summary += "This is a small project with relatively simple structure."
        
        summary['text'] = text_summary
        
        return summary 