import os
import re
import json
from collections import defaultdict, Counter

class ProjectReviewer:
    """
    Generates comprehensive project reviews and reports
    """
    
    def __init__(self, code_analyzer=None, ai_analyzer=None):
        """Initialize the project reviewer"""
        self.code_analyzer = code_analyzer
        self.ai_analyzer = ai_analyzer
        
    def generate_full_review(self, file_analyses):
        """
        Generate a comprehensive project review
        Returns a structured review with insights and recommendations
        """
        # Basic project summary
        if self.code_analyzer:
            basic_summary = self.code_analyzer.generate_project_summary(file_analyses)
        else:
            basic_summary = self._generate_basic_summary(file_analyses)
        
        # AI-enhanced summary if available
        ai_summary = {}
        if self.ai_analyzer:
            ai_result = self.ai_analyzer.generate_project_summary(file_analyses)
            ai_summary = ai_result.get('ai_summary', {})
        
        # Generate architecture insights
        architecture = self._analyze_architecture(file_analyses)
        
        # Generate code quality assessment
        code_quality = self._assess_code_quality(file_analyses, ai_summary)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            file_analyses, basic_summary, ai_summary, architecture, code_quality)
        
        # Combine into full review
        full_review = {
            'basic_summary': basic_summary,
            'ai_summary': ai_summary,
            'architecture': architecture,
            'code_quality': code_quality,
            'recommendations': recommendations
        }
        
        return full_review
    
    def _generate_basic_summary(self, file_analyses):
        """Generate a basic project summary without the code analyzer"""
        languages = {}
        file_count = len(file_analyses)
        total_lines = 0
        class_count = 0
        function_count = 0
        
        for analysis in file_analyses:
            # Count languages
            lang = analysis.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
            
            # Count lines
            total_lines += analysis.get('line_count', 0)
            
            # Count classes and functions
            elements = analysis.get('elements', [])
            class_count += sum(1 for e in elements if e['type'] == 'class')
            function_count += sum(1 for e in elements if e['type'] == 'function')
        
        # Generate a text summary
        if file_count > 0:
            main_lang = max(languages.items(), key=lambda x: x[1])[0]
            text = f"This project contains {file_count} files primarily written in {main_lang}. "
            text += f"It has {class_count} classes and {function_count} functions across {total_lines} lines of code."
        else:
            text = "No files were analyzed for this project."
            
        return {
            'text': text,
            'file_count': file_count,
            'total_lines': total_lines,
            'class_count': class_count,
            'function_count': function_count,
            'languages': languages
        }
    
    def _analyze_architecture(self, file_analyses):
        """Analyze the project's architecture and structure"""
        # Group files by directory
        directories = defaultdict(list)
        for analysis in file_analyses:
            path = analysis['path']
            dir_path = os.path.dirname(path)
            if not dir_path:
                dir_path = '/'  # Root directory
            directories[dir_path].append(path)
        
        # Calculate directory metrics
        dir_metrics = {}
        for dir_path, files in directories.items():
            dir_metrics[dir_path] = {
                'file_count': len(files),
                'files': [os.path.basename(f) for f in files]
            }
        
        # Identify main components based on directories
        components = []
        for dir_path, metrics in dir_metrics.items():
            if metrics['file_count'] >= 2:  # Consider it a component if it has at least 2 files
                components.append({
                    'name': dir_path.lstrip('/').replace('/', '.') or 'root',
                    'file_count': metrics['file_count'],
                    'files': metrics['files'][:5]  # Limit to 5 example files
                })
        
        # Sort components by file count
        components.sort(key=lambda x: x['file_count'], reverse=True)
        
        # Analyze dependencies between components (simplified)
        dependencies = []
        for analysis in file_analyses:
            source_dir = os.path.dirname(analysis['path'])
            if not source_dir:
                source_dir = '/'
                
            # Check imports
            for imp in analysis.get('imports', []):
                # Simple heuristic to match imports to directories
                for target_dir in directories.keys():
                    if target_dir != source_dir and self._is_import_from_dir(imp, target_dir, directories[target_dir]):
                        dependencies.append({
                            'source': source_dir.lstrip('/').replace('/', '.') or 'root',
                            'target': target_dir.lstrip('/').replace('/', '.') or 'root'
                        })
                        break
        
        # Remove duplicates from dependencies
        unique_deps = []
        seen = set()
        for dep in dependencies:
            key = f"{dep['source']}->{dep['target']}"
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return {
            'directories': dir_metrics,
            'components': components[:10],  # Limit to top 10 components
            'dependencies': unique_deps
        }
    
    def _is_import_from_dir(self, import_str, directory, dir_files):
        """Check if an import likely refers to a file in the directory"""
        # Extract the imported name
        import_patterns = [
            r'import\s+([^\s,;]+)',
            r'from\s+([^\s,;]+)\s+import',
            r'require\([\'"]\s*([^\s,;\'"]*)[\'"]\)',
            r'#include\s+[<"]([^>"]+)[>"]'
        ]
        
        for pattern in import_patterns:
            match = re.search(pattern, import_str)
            if match:
                imported = match.group(1)
                
                # Check files in the directory
                for file in dir_files:
                    file_base = os.path.splitext(os.path.basename(file))[0]
                    
                    # Convert dot notation to path components
                    imported_parts = imported.split('.')
                    
                    # Check for match
                    if file_base == imported or file_base == imported_parts[-1]:
                        return True
                
                # Check if directory name is in the import path
                dir_name = os.path.basename(directory.rstrip('/'))
                if dir_name and dir_name in imported.split('.'):
                    return True
                    
        return False
    
    def _assess_code_quality(self, file_analyses, ai_summary=None):
        """Assess overall code quality"""
        # Calculate basic metrics
        comment_ratio = 0
        complexity = 0
        analyzed_files = 0
        
        for analysis in file_analyses:
            if 'comment_ratio' in analysis:
                comment_ratio += analysis['comment_ratio']
                analyzed_files += 1
            
            if 'ai_insights' in analysis and 'complexity' in analysis['ai_insights']:
                complexity += analysis['ai_insights']['complexity'].get('cyclomatic', 0)
        
        if analyzed_files > 0:
            avg_comment_ratio = comment_ratio / analyzed_files
            avg_complexity = complexity / analyzed_files
        else:
            avg_comment_ratio = 0
            avg_complexity = 0
        
        # Determine ratings
        documentation_rating = 'good' if avg_comment_ratio > 0.15 else ('fair' if avg_comment_ratio > 0.05 else 'poor')
        complexity_rating = 'good' if avg_complexity < 5 else ('fair' if avg_complexity < 10 else 'poor')
        
        # Use AI quality score if available
        quality_score = ai_summary.get('quality_score', 0)
        overall_rating = 'good' if quality_score > 80 else ('fair' if quality_score > 60 else 'poor')
        
        # Count issues
        code_smells = len(ai_summary.get('code_smells', {}))
        security_issues = len(ai_summary.get('security_issues', {}))
        
        return {
            'metrics': {
                'comment_ratio': round(avg_comment_ratio, 2),
                'complexity': round(avg_complexity, 2),
                'quality_score': quality_score,
                'code_smells': code_smells,
                'security_issues': security_issues
            },
            'ratings': {
                'documentation': documentation_rating,
                'complexity': complexity_rating,
                'overall': overall_rating
            }
        }
    
    def _generate_recommendations(self, file_analyses, basic_summary, ai_summary, architecture, code_quality):
        """Generate actionable recommendations for the project"""
        recommendations = []
        
        # Add AI recommendations if available
        if 'recommendations' in ai_summary:
            recommendations.extend(ai_summary['recommendations'])
        
        # Add recommendations based on code quality
        ratings = code_quality['ratings']
        
        if ratings['documentation'] == 'poor':
            recommendations.append({
                'type': 'documentation',
                'message': 'Improve code documentation by adding more comments and docstrings.'
            })
        
        if ratings['complexity'] == 'poor':
            recommendations.append({
                'type': 'complexity',
                'message': 'Refactor complex functions to improve maintainability.'
            })
        
        # Add architecture recommendations
        if len(architecture['components']) > 10:
            recommendations.append({
                'type': 'architecture',
                'message': 'Consider consolidating similar components to simplify the project structure.'
            })
        
        # Check for too many dependencies
        if len(architecture['dependencies']) > len(architecture['components']) * 2:
            recommendations.append({
                'type': 'architecture',
                'message': 'Reduce coupling between components to improve modularity.'
            })
        
        # Check for inconsistent naming patterns
        if self._has_inconsistent_naming(file_analyses):
            recommendations.append({
                'type': 'naming',
                'message': 'Standardize naming conventions across the project for better readability.'
            })
        
        # Add testing recommendation if no test files found
        if not self._has_tests(file_analyses):
            recommendations.append({
                'type': 'testing',
                'message': 'Add unit tests to improve code reliability and facilitate future changes.'
            })
        
        # Add security recommendations if needed
        if code_quality['metrics']['security_issues'] > 0:
            recommendations.append({
                'type': 'security',
                'message': 'Address identified security vulnerabilities as a priority.'
            })
        
        return recommendations
    
    def _has_inconsistent_naming(self, file_analyses):
        """Check for inconsistent naming patterns"""
        # Look at function names to detect inconsistency
        naming_styles = {
            'snake_case': 0,
            'camelCase': 0,
            'PascalCase': 0
        }
        
        for analysis in file_analyses:
            for element in analysis.get('elements', []):
                if element['type'] == 'function':
                    name = element['name']
                    if '_' in name:
                        naming_styles['snake_case'] += 1
                    elif name[0].isupper():
                        naming_styles['PascalCase'] += 1
                    elif name[0].islower() and any(c.isupper() for c in name):
                        naming_styles['camelCase'] += 1
        
        # Check if multiple styles are used significantly
        total = sum(naming_styles.values())
        return total > 10 and all(count > total * 0.2 for count in naming_styles.values() if count > 0)
    
    def _has_tests(self, file_analyses):
        """Check if the project has test files"""
        for analysis in file_analyses:
            path = analysis['path'].lower()
            if 'test' in path or 'spec' in path:
                return True
                
            # Check for test imports/functions
            for element in analysis.get('elements', []):
                if element['type'] == 'import' and ('test' in element['name'].lower() or 'pytest' in element['name'].lower()):
                    return True
                if element['type'] == 'function' and (element['name'].startswith('test_') or element['name'].startswith('should_')):
                    return True
        
        return False
