# src/ai_analyzer/__init__.py
# AI-driven code analysis module for P2R

import os
import re
import ast
import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict, Counter
import networkx as nx
import subprocess
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class AICodeAnalyzer:
    """
    AI-driven code analysis module inspired by Coderabbit.ai
    Provides deeper insights through machine learning and static analysis
    """
    
    def __init__(self):
        """Initialize the AI code analyzer with ML tools and patterns"""
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.code_patterns = self._load_code_patterns()
        self.security_patterns = self._load_security_patterns()
        self.quality_metrics = {}
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
    def _load_code_patterns(self):
        """Load patterns for code smell detection"""
        return {
            'long_method': {
                'pattern': r'def\s+\w+\s*\([^)]*\)[^{]*\{[^}]{500,}\}',
                'message': 'Method is too long (>500 characters). Consider breaking it down.'
            },
            'complex_condition': {
                'pattern': r'if\s+[^{:]*?(?:&&|\|\|)[^{:]*?(?:&&|\|\|)[^{:]*?(?:&&|\|\|)',
                'message': 'Complex condition with 3+ logical operators. Consider simplifying.'
            },
            'magic_number': {
                'pattern': r'(?<!\w)(?<!\.)(?<!-)\d{4,}(?!\w)(?!\.)(?!-)(?!\s*[\/\*\+\-])',
                'message': 'Magic number detected. Consider using a named constant.'
            },
            'duplicate_code': {
                'pattern': None,  # Handled separately via similarity analysis
                'message': 'Duplicate or very similar code detected.'
            }
        }
    
    def _load_security_patterns(self):
        """Load patterns for security vulnerability detection"""
        return {
            'sql_injection': {
                'pattern': r'execute\(\s*[\'"][^\'")]*\s*\'\s*\+|cursor\.execute\s*\(\s*[^,)]+\s*%\s*[^,)]+\)',
                'message': 'Potential SQL injection vulnerability detected. Use parameterized queries.'
            },
            'command_injection': {
                'pattern': r'os\.system\(\s*[^)]*\+|subprocess\.(?:call|run|Popen)\(\s*[^),]*\+',
                'message': 'Potential command injection vulnerability. Avoid string concatenation.'
            },
            'hardcoded_secret': {
                'pattern': r'(?:password|token|secret|key)\s*=\s*[\'"][^\'"]{8,}[\'"]',
                'message': 'Possible hardcoded secret detected. Use environment variables instead.'
            },
            'insecure_hash': {
                'pattern': r'hashlib\.(?:md5|sha1)\(',
                'message': 'Insecure hash algorithm (MD5/SHA1) detected. Use SHA-256 or better.'
            }
        }
    
    def analyze_file(self, file_path, content):
        """
        Perform AI-enhanced analysis on a file
        Returns enhanced analysis results with ML-based insights
        """
        # Basic analysis
        language = os.path.splitext(file_path)[1].lstrip('.')
        analysis = {
            'path': file_path,
            'language': language,
            'size': len(content.encode('utf-8')),
            'ai_insights': {
                'code_smells': [],
                'security_issues': [],
                'quality_score': 0,
                'complexity': self._calculate_complexity(content, language),
                'concepts': self._extract_key_concepts(content),
                'improvement_suggestions': []
            }
        }
        
        # Detect code smells
        analysis['ai_insights']['code_smells'] = self._detect_code_smells(content)
        
        # Detect security issues
        analysis['ai_insights']['security_issues'] = self._detect_security_issues(content)
        
        # Calculate quality score (0-100)
        analysis['ai_insights']['quality_score'] = self._calculate_quality_score(content, analysis)
        
        # Generate improvements
        analysis['ai_insights']['improvement_suggestions'] = self._generate_improvements(content, analysis)
        
        return analysis
    
    def _detect_code_smells(self, content):
        """Detect common code smells in the content"""
        smells = []
        
        # Regex-based detection
        for smell_name, info in self.code_patterns.items():
            if info['pattern'] is None:
                continue  # Skip patterns handled separately
                
            matches = re.finditer(info['pattern'], content, re.MULTILINE | re.DOTALL)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                smells.append({
                    'type': smell_name,
                    'message': info['message'],
                    'line': line_number,
                    'severity': 'medium'
                })
        
        # Python-specific AST-based analysis
        try:
            tree = ast.parse(content)
            
            # Find functions with too many arguments
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.args.args) > 5:  # More than 5 arguments
                        smells.append({
                            'type': 'too_many_arguments',
                            'message': f'Function {node.name} has {len(node.args.args)} parameters. Consider refactoring.',
                            'line': node.lineno,
                            'severity': 'medium'
                        })
        except Exception:
            # If AST parsing fails, skip this part of the analysis
            pass
            
        return smells
    
    def _detect_security_issues(self, content):
        """Detect security vulnerabilities in the content"""
        issues = []
        
        for issue_name, info in self.security_patterns.items():
            matches = re.finditer(info['pattern'], content, re.MULTILINE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': issue_name,
                    'message': info['message'],
                    'line': line_number,
                    'severity': 'high'
                })
                
        return issues
    
    def _calculate_complexity(self, content, language):
        """Calculate code complexity metrics"""
        # Count decision points as a simple complexity metric
        decision_patterns = {
            'if': r'\bif\b',
            'for': r'\bfor\b',
            'while': r'\bwhile\b',
            'switch': r'\bswitch\b',
            'catch': r'\bcatch\b'
        }
        
        complexity = 0
        for pattern in decision_patterns.values():
            complexity += len(re.findall(pattern, content))
            
        # Nested depth calculation
        max_indent = 0
        current_indent = 0
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped and not stripped.startswith(('#', '//', '/*', '*')):  # Skip comments
                indent = len(line) - len(stripped)
                current_indent = indent // 4  # Assuming 4 spaces per indent level
                max_indent = max(max_indent, current_indent)
        
        return {
            'cyclomatic': complexity,
            'max_nested_depth': max_indent,
            'rating': self._complexity_rating(complexity)
        }
    
    def _complexity_rating(self, complexity):
        """Convert complexity value to a rating"""
        if complexity < 5:
            return 'low'
        elif complexity < 10:
            return 'medium'
        else:
            return 'high'
    
    def _extract_key_concepts(self, content):
        """Extract key concepts from the code using NLP techniques"""
        # Extract words from identifiers
        words = []
        
        # Extract identifiers (variable names, function names, etc.)
        identifier_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        identifiers = re.findall(identifier_pattern, content)
        
        # Split camelCase and snake_case identifiers into words
        for identifier in identifiers:
            # Split snake_case
            snake_split = identifier.split('_')
            
            # Split camelCase
            camel_split = []
            for word in snake_split:
                if word:
                    splits = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)
                    camel_split.extend(splits)
            
            words.extend([w.lower() for w in camel_split if w.lower() not in self.stopwords and len(w) > 2])
        
        # Count word frequency
        word_counts = Counter(words)
        
        # Return top concepts
        return [{'word': word, 'count': count} 
                for word, count in word_counts.most_common(10)]
    
    def _calculate_quality_score(self, content, analysis):
        """Calculate an overall quality score (0-100)"""
        # Base score
        score = 100
        
        # Deduct for code smells
        score -= len(analysis['ai_insights']['code_smells']) * 5
        
        # Deduct more for security issues
        score -= len(analysis['ai_insights']['security_issues']) * 10
        
        # Deduct for complexity
        complexity = analysis['ai_insights']['complexity']['cyclomatic']
        if complexity > 15:
            score -= 20
        elif complexity > 10:
            score -= 10
        elif complexity > 5:
            score -= 5
        
        # Ensure score is between 0 and 100
        return max(0, min(score, 100))
    
    def _generate_improvements(self, content, analysis):
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Add specific improvements based on detected issues
        for smell in analysis['ai_insights']['code_smells']:
            suggestions.append({
                'type': 'code_smell',
                'message': smell['message'],
                'line': smell['line'],
                'priority': 'medium'
            })
            
        for issue in analysis['ai_insights']['security_issues']:
            suggestions.append({
                'type': 'security',
                'message': issue['message'],
                'line': issue['line'],
                'priority': 'high'
            })
        
        # Add general improvements based on code patterns
        if analysis['ai_insights']['complexity']['rating'] == 'high':
            suggestions.append({
                'type': 'refactoring',
                'message': 'Consider refactoring complex code sections into smaller, more manageable functions.',
                'line': None,
                'priority': 'medium'
            })
        
        # Check for meaningful variable names (heuristic)
        short_var_pattern = r'\b([a-z_]{1,2})\s*='
        short_vars = re.findall(short_var_pattern, content)
        if short_vars:
            suggestions.append({
                'type': 'naming',
                'message': 'Consider using more descriptive variable names instead of short abbreviations.',
                'line': None,
                'priority': 'low'
            })
            
        return suggestions
        
    def generate_project_summary(self, file_analyses):
        """
        Generate a comprehensive project summary with AI insights
        """
        all_code_smells = []
        all_security_issues = []
        all_concepts = []
        total_files = len(file_analyses)
        quality_scores = []
        
        # Collect data from all files
        for analysis in file_analyses:
            if 'ai_insights' in analysis:
                all_code_smells.extend(analysis['ai_insights']['code_smells'])
                all_security_issues.extend(analysis['ai_insights']['security_issues'])
                all_concepts.extend(analysis['ai_insights']['concepts'])
                quality_scores.append(analysis['ai_insights']['quality_score'])
        
        # Calculate averages
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Get top concepts project-wide
        concept_counter = Counter()
        for concept in all_concepts:
            concept_counter[concept['word']] += concept['count']
        
        top_concepts = [{'word': word, 'count': count} 
                       for word, count in concept_counter.most_common(10)]
        
        # Group code smells and security issues by type
        smell_types = defaultdict(int)
        for smell in all_code_smells:
            smell_types[smell['type']] += 1
            
        security_types = defaultdict(int)
        for issue in all_security_issues:
            security_types[issue['type']] += 1
        
        # Generate recommendations based on findings
        recommendations = self._generate_project_recommendations(
            smell_types, security_types, avg_quality)
        
        return {
            'ai_summary': {
                'quality_score': round(avg_quality, 1),
                'code_smells': dict(smell_types),
                'security_issues': dict(security_types),
                'key_concepts': top_concepts,
                'recommendations': recommendations
            }
        }
        
    def _generate_project_recommendations(self, smell_types, security_types, avg_quality):
        """Generate project-level recommendations based on findings"""
        recommendations = []
        
        # Add recommendations based on detected issue patterns
        if security_types:
            recommendations.append({
                'type': 'security',
                'message': 'Implement a security scanning process in your CI/CD pipeline to catch potential vulnerabilities early.'
            })
            
        if smell_types.get('duplicate_code', 0) > 5:
            recommendations.append({
                'type': 'refactoring',
                'message': 'Consider creating shared utility functions or classes to reduce code duplication.'
            })
            
        if smell_types.get('complex_condition', 0) > 3:
            recommendations.append({
                'type': 'complexity',
                'message': 'Review complex conditional logic throughout the project and consider refactoring using strategy pattern or lookup tables.'
            })
            
        if avg_quality < 70:
            recommendations.append({
                'type': 'quality',
                'message': 'Set up linting and code quality tools in your development workflow to maintain higher code standards.'
            })
            
        return recommendations
        
    def analyze_code_similarity(self, file_analyses):
        """
        Analyze code similarity across the project to detect duplicated code
        """
        # Extract content from analyses
        contents = []
        paths = []
        for analysis in file_analyses:
            if 'content' in analysis:
                contents.append(analysis['content'])
                paths.append(analysis['path'])
        
        # If there are enough files to compare
        if len(contents) < 2:
            return []
            
        # Vectorize the code
        try:
            X = self.vectorizer.fit_transform(contents)
            
            # Calculate similarity matrix
            similarity_matrix = (X * X.T).toarray()
            
            # Find pairs with high similarity (but not identical)
            similar_pairs = []
            for i in range(len(paths)):
                for j in range(i+1, len(paths)):
                    similarity = similarity_matrix[i][j]
                    if 0.7 < similarity < 0.99:  # High similarity but not identical
                        similar_pairs.append({
                            'file1': paths[i],
                            'file2': paths[j],
                            'similarity': round(similarity, 2)
                        })
            
            return similar_pairs
        except:
            # If vectorization fails, return empty result
            return []
            
    def run_security_scan(self, project_dir):
        """
        Run a comprehensive security scan using bandit
        """
        try:
            # Run bandit security scanner
            result = subprocess.run(
                ['bandit', '-r', project_dir, '-f', 'json'],
                capture_output=True,
                text=True
            )
            
            # Parse the results
            if result.returncode in [0, 1]:  # 0=no issues, 1=issues found
                try:
                    data = json.loads(result.stdout)
                    security_issues = []
                    
                    # Extract relevant information
                    for result in data.get('results', []):
                        issue = {
                            'file': result.get('filename'),
                            'line': result.get('line_number'),
                            'issue_type': result.get('issue_text'),
                            'severity': result.get('issue_severity', 'medium'),
                            'confidence': result.get('issue_confidence', 'medium')
                        }
                        security_issues.append(issue)
                        
                    return security_issues
                except json.JSONDecodeError:
                    return []
            
            return []
        except Exception as e:
            print(f"Security scan error: {str(e)}")
            return []
