import re
import ast
import builtins
import difflib

class CodeQA:
    """
    Module for interactive questions and answers about the code
    """
    
    def __init__(self):
        """Initialize the code QA module"""
        self.file_contents = {}  # Store file contents for reference
        self.file_analyses = {}  # Store analysis results
        
        # Known Python built-ins and common libraries
        self.builtins = dir(builtins)
        self.common_libraries = [
            'os', 'sys', 'time', 're', 'datetime', 'collections', 'json',
            'math', 'random', 'itertools', 'functools', 'pathlib', 'subprocess'
        ]
    
    def load_project_data(self, file_analyses, file_contents):
        """Load project data for reference during Q&A"""
        self.file_analyses = {analysis['path']: analysis for analysis in file_analyses}
        self.file_contents = file_contents
    
    def answer_question(self, question):
        """
        Answer a natural language question about the code
        Returns a response and relevant code references
        """
        question = question.lower().strip()
        
        # Define question patterns and their handlers
        patterns = [
            (r'what (does|is) ([^?]+)( do| for)?', self._answer_what_is),
            (r'how (does|is|are) ([^?]+)( work| implemented)?', self._answer_how_works),
            (r'where is ([^?]+?)( used| called| implemented| defined)?', self._answer_where_is),
            (r'why (does|is) ([^?]+)', self._answer_why),
            (r'list all ([^?]+)', self._answer_list_all),
            (r'explain ([^?]+)', self._answer_explain),
            (r'compare ([^?]+) (?:with|and|to) ([^?]+)', self._answer_compare)
        ]
        
        # Try to match the question and call the appropriate handler
        for pattern, handler in patterns:
            match = re.search(pattern, question)
            if match:
                return handler(match, question)
        
        # Default response for unmatched questions
        return self._answer_generic(question)
    
    def _answer_what_is(self, match, question):
        """Handle 'what is/does' questions"""
        subject = match.group(2).strip()
        
        # Check if it's asking about a specific function, class, or file
        found_items = self._find_code_elements(subject)
        
        if found_items:
            item = found_items[0]
            if item['type'] == 'function':
                return self._describe_function(item)
            elif item['type'] == 'class':
                return self._describe_class(item)
            elif item['type'] == 'file':
                return self._describe_file(item)
        
        # Check if asking about a concept or pattern
        return self._describe_concept(subject)
    
    def _answer_how_works(self, match, question):
        """Handle 'how does' questions"""
        subject = match.group(2).strip()
        
        # Check if it's asking about a specific function, class, or file
        found_items = self._find_code_elements(subject)
        
        if found_items:
            item = found_items[0]
            if item['type'] == 'function':
                return self._explain_function_logic(item)
            elif item['type'] == 'class':
                return self._explain_class_logic(item)
            elif item['type'] == 'file':
                return self._explain_file_logic(item)
        
        # Check if asking about a process or flow
        if 'data flow' in subject or 'process' in subject:
            return self._explain_data_flow(subject)
            
        return {
            'answer': f"I don't have enough information to explain how '{subject}' works in this codebase.",
            'references': []
        }
    
    def _answer_where_is(self, match, question):
        """Handle 'where is' questions"""
        subject = match.group(1).strip()
        action = match.group(2).strip() if match.group(2) else ''
        
        locations = []
        
        # Different logic based on whether we're looking for usage or definition
        if 'used' in action or 'called' in action:
            locations = self._find_usage_locations(subject)
        else:  # Looking for definition/implementation
            found_items = self._find_code_elements(subject)
            if found_items:
                for item in found_items:
                    locations.append({
                        'file': item['file'],
                        'line': item['line'],
                        'context': item.get('context', f"Definition of {subject}")
                    })
        
        if locations:
            if len(locations) == 1:
                answer = f"'{subject}' is located in {locations[0]['file']} at line {locations[0]['line']}."
            else:
                answer = f"'{subject}' is found in {len(locations)} locations:"
                
            return {
                'answer': answer,
                'references': locations
            }
        else:
            return {
                'answer': f"I couldn't find '{subject}' in the codebase.",
                'references': []
            }
    
    def _answer_why(self, match, question):
        """Handle 'why does/is' questions"""
        subject = match.group(2).strip()
        
        # Try to find relevant code elements
        found_items = self._find_code_elements(subject)
        
        if found_items:
            # Get the first matching item
            item = found_items[0]
            
            # Extract comments above the element that might explain reasoning
            comments = self._extract_nearby_comments(item['file'], item['line'])
            
            if comments:
                return {
                    'answer': f"The code documentation suggests: {comments}",
                    'references': [{
                        'file': item['file'],
                        'line': item['line'],
                        'context': item.get('context', subject)
                    }]
                }
        
        # If we couldn't find a direct answer, try to infer from code patterns
        inferred_reason = self._infer_reasoning(subject, question)
        if inferred_reason:
            return {
                'answer': inferred_reason,
                'references': [ref for item in found_items for ref in [{
                    'file': item['file'],
                    'line': item['line'],
                    'context': item.get('context', subject)
                }]]
            }
        
        return {
            'answer': f"I don't have enough information to explain why '{subject}' is implemented this way.",
            'references': []
        }
    
    def _answer_list_all(self, match, question):
        """Handle 'list all' questions"""
        subject = match.group(1).strip()
        
        items = []
        
        # Different handling based on what we're listing
        if 'function' in subject or 'method' in subject:
            for path, analysis in self.file_analyses.items():
                for element in analysis.get('elements', []):
                    if element['type'] == 'function':
                        items.append({
                            'name': element['name'],
                            'file': path,
                            'line': element.get('line', 0)
                        })
        
        elif 'class' in subject:
            for path, analysis in self.file_analyses.items():
                for element in analysis.get('elements', []):
                    if element['type'] == 'class':
                        items.append({
                            'name': element['name'],
                            'file': path,
                            'line': element.get('line', 0)
                        })
        
        elif 'file' in subject:
            items = [{'name': path, 'file': path, 'line': 0} for path in self.file_analyses.keys()]
        
        elif 'import' in subject:
            for path, analysis in self.file_analyses.items():
                for imp in analysis.get('imports', []):
                    items.append({
                        'name': imp,
                        'file': path,
                        'line': 0
                    })
        
        if items:
            answer = f"Found {len(items)} {subject}:"
            references = [{
                'file': item['file'],
                'line': item['line'],
                'context': item['name']
            } for item in items[:10]]  # Limit to 10 references
            
            return {
                'answer': answer,
                'references': references,
                'count': len(items)
            }
        else:
            return {
                'answer': f"No {subject} found in the codebase.",
                'references': []
            }
    
    def _find_code_elements(self, subject):
        """Find code elements matching the subject name"""
        subject = subject.strip().lower()
        results = []
        
        # Search through all files and their elements
        for path, analysis in self.file_analyses.items():
            # Check if the subject refers to this file
            if subject in path.lower():
                results.append({
                    'type': 'file',
                    'name': path,
                    'file': path,
                    'line': 1,
                    'context': f"File: {path}"
                })
            
            # Check elements within the file
            for element in analysis.get('elements', []):
                element_name = element.get('name', '').lower()
                if subject == element_name or subject in element_name:
                    results.append({
                        'type': element['type'],
                        'name': element['name'],
                        'file': path,
                        'line': element.get('line', 0),
                        'context': f"{element['type'].capitalize()}: {element['name']}"
                    })
        
        # Sort by relevance (exact match first, then partial matches)
        results.sort(key=lambda x: 0 if x['name'].lower() == subject else 1)
        
        return results
    
    def _describe_file(self, item):
        """Generate a description of a file"""
        file_path = item['file']
        
        if file_path not in self.file_analyses:
            return {
                'answer': f"File '{file_path}' exists but I couldn't analyze its content.",
                'references': [{'file': file_path, 'line': 1, 'context': file_path}]
            }
        
        analysis = self.file_analyses[file_path]
        
        # Count elements by type
        element_counts = {}
        for element in analysis.get('elements', []):
            element_type = element['type']
            element_counts[element_type] = element_counts.get(element_type, 0) + 1
        
        # Basic description
        description = f"File '{file_path}' ({analysis.get('language', 'Unknown language')})"
        
        # Add counts
        details = []
        if element_counts.get('class', 0) > 0:
            details.append(f"{element_counts['class']} classes")
        if element_counts.get('function', 0) > 0:
            details.append(f"{element_counts['function']} functions")
        if element_counts.get('import', 0) > 0:
            details.append(f"{element_counts['import']} imports")
            
        if details:
            description += f" contains {', '.join(details)}"
            
        # Add summary if available
        if 'summary' in analysis:
            description += f". Summary: {analysis['summary']}"
        
        return {
            'answer': description,
            'references': [{'file': file_path, 'line': 1, 'context': file_path}]
        }
    
    def _explain_specific_line(self, file_name, line_num):
        """Explain a specific line of code"""
        matching_files = []
        for path in self.file_contents:
            if file_name in path:
                matching_files.append(path)
        
        if not matching_files:
            return {
                'answer': f"I couldn't find a file matching '{file_name}'.",
                'references': []
            }
        
        file_path = matching_files[0]  # Use the first matching file
        
        if file_path not in self.file_contents:
            return {
                'answer': f"File '{file_path}' exists but I couldn't access its content.",
                'references': [{'file': file_path, 'line': line_num, 'context': ''}]
            }
        
        content = self.file_contents[file_path]
        lines = content.splitlines()
        
        if line_num < 1 or line_num > len(lines):
            return {
                'answer': f"Line {line_num} is out of range for file '{file_path}'.",
                'references': [{'file': file_path, 'line': 1, 'context': ''}]
            }
        
        # Get the line and some context
        line = lines[line_num - 1]
        context = self._get_context_lines(content, line_num)
        
        # Simple explanation based on the line content
        explanation = f"Line {line_num} contains: {line.strip()}. "
        
        # Add more context based on the line type
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            explanation += "This defines a function."
        elif re.match(r'^\s*class\s+\w+', line):
            explanation += "This defines a class."
        elif re.match(r'^\s*if\s+', line):
            explanation += "This is a conditional statement."
        elif re.match(r'^\s*for\s+', line):
            explanation += "This is a loop statement."
        elif re.match(r'^\s*return\s+', line):
            explanation += "This returns a value from a function."
        elif re.match(r'^\s*import\s+', line) or re.match(r'^\s*from\s+\w+\s+import', line):
            explanation += "This imports external modules or functions."
        
        return {
            'answer': explanation,
            'references': [{'file': file_path, 'line': line_num, 'context': context}]
        }
    
    def _compare_functions(self, func1, func2):
        """Compare two functions"""
        # Extract function codes
        code1 = self._extract_function_code(func1['file'], func1['line'])
        code2 = self._extract_function_code(func2['file'], func2['line'])
        
        if not code1 or not code2:
            return f"I couldn't extract the code for one or both functions to compare them."
        
        # Compare parameters
        params1 = self._extract_function_params(func1['file'], func1['line'])
        params2 = self._extract_function_params(func2['file'], func2['line'])
        
        # Calculate code similarity using difflib
        similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
        similarity_percentage = round(similarity * 100, 1)
        
        # Prepare comparison response
        comparison = [f"Functions '{func1['name']}' and '{func2['name']}' are {similarity_percentage}% similar."]
        
        # Compare parameters
        if params1 == params2:
            comparison.append(f"Both functions take the same parameters: {', '.join(params1) if params1 else 'none'}.")
        else:
            comparison.append(f"'{func1['name']}' takes parameters: {', '.join(params1) if params1 else 'none'}.")
            comparison.append(f"'{func2['name']}' takes parameters: {', '.join(params2) if params2 else 'none'}.")
        
        # Check if one is potentially a modified version of the other
        if similarity > 0.7:
            comparison.append("These functions appear to be related or different versions of the same functionality.")
        
        # Check for common patterns in both
        patterns = [
            ('return', 'Both functions return values.'),
            ('if', 'Both functions contain conditional logic.'),
            ('for', 'Both functions contain loops.'),
            ('try', 'Both functions include error handling.')
        ]
        
        for pattern, message in patterns:
            if pattern in code1 and pattern in code2:
                comparison.append(message)
        
        return ' '.join(comparison)
    
    def _compare_classes(self, cls1, cls2):
        """Compare two classes"""
        # Extract methods
        methods1 = self._extract_class_methods(cls1['file'], cls1['name'])
        methods2 = self._extract_class_methods(cls2['file'], cls2['name'])
        
        # Calculate similarity based on methods
        common_methods = set(methods1).intersection(set(methods2))
        all_methods = set(methods1).union(set(methods2))
        similarity = len(common_methods) / len(all_methods) if all_methods else 0
        similarity_percentage = round(similarity * 100, 1)
        
        # Prepare comparison response
        comparison = [f"Classes '{cls1['name']}' and '{cls2['name']}' share {similarity_percentage}% of their methods."]
        
        if common_methods:
            comparison.append(f"Common methods: {', '.join(common_methods)}.")
        
        methods_only_in_1 = set(methods1) - set(methods2)
        if methods_only_in_1:
            comparison.append(f"Methods only in '{cls1['name']}': {', '.join(methods_only_in_1)}.")
            
        methods_only_in_2 = set(methods2) - set(methods1)
        if methods_only_in_2:
            comparison.append(f"Methods only in '{cls2['name']}': {', '.join(methods_only_in_2)}.")
        
        return ' '.join(comparison)
    
    def _compare_files(self, file1, file2):
        """Compare two files"""
        path1, path2 = file1['file'], file2['file']
        
        if path1 not in self.file_analyses or path2 not in self.file_analyses:
            return f"I couldn't analyze one or both files to compare them."
        
        analysis1 = self.file_analyses[path1]
        analysis2 = self.file_analyses[path2]
        
        # Get element counts
        element_types = ['class', 'function', 'import', 'variable']
        counts1 = {t: sum(1 for e in analysis1.get('elements', []) if e['type'] == t) for t in element_types}
        counts2 = {t: sum(1 for e in analysis2.get('elements', []) if e['type'] == t) for t in element_types}
        
        # Get element names for comparison
        elements1 = {t: [e['name'] for e in analysis1.get('elements', []) if e['type'] == t] for t in element_types}
        elements2 = {t: [e['name'] for e in analysis2.get('elements', []) if e['type'] == t] for t in element_types}
        
        # Calculate similarity based on shared element names
        all_names1 = [e['name'] for e in analysis1.get('elements', [])]
        all_names2 = [e['name'] for e in analysis2.get('elements', [])]
        
        common_names = set(all_names1).intersection(set(all_names2))
        all_names = set(all_names1).union(set(all_names2))
        
        similarity = len(common_names) / len(all_names) if all_names else 0
        similarity_percentage = round(similarity * 100, 1)
        
        # Prepare comparison response
        comparison = [f"Files '{path1}' and '{path2}' share {similarity_percentage}% of their code elements."]
        
        # Compare element counts
        for element_type in element_types:
            if counts1[element_type] > 0 or counts2[element_type] > 0:
                comparison.append(f"'{path1}' has {counts1[element_type]} {element_type}s, '{path2}' has {counts2[element_type]}.")
        
        # List some common elements
        if common_names:
            sample = list(common_names)[:5]  # Limit to 5 examples
            comparison.append(f"Common elements include: {', '.join(sample)}" + 
                             (f" and {len(common_names) - 5} others" if len(common_names) > 5 else "."))
        
        return ' '.join(comparison)
    
    def _answer_explain(self, match, question):
        """Answer questions about explaining parts of the code"""
        topic = match.group(1).strip()
        
        # Search for the topic in the code
        relevant_files = []
        for file_analysis in self.file_analyses:
            content = self.get_file_content(file_analysis['path'])
            if not content:
                continue
            
            if topic.lower() in content.lower():
                relevant_files.append({
                    'file': file_analysis['path'],
                    'content': content
                })
        
        if not relevant_files:
            return {
                'answer': f"I couldn't find any code related to '{topic}' in the project.",
                'references': []
            }
        
        # Generate an explanation based on the found files
        explanation = f"Here's an explanation of '{topic}':\n\n"
        references = []
        
        for file_info in relevant_files[:3]:  # Limit to 3 references
            file_path = file_info['file']
            content = file_info['content']
            
            # Find the most relevant section
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if topic.lower() in line.lower():
                    start_line = max(0, i - 5)
                    end_line = min(len(lines), i + 5)
                    context = '\n'.join(lines[start_line:end_line])
                    
                    references.append({
                        'file': file_path,
                        'line': i + 1,
                        'context': context
                    })
                    break
        
        explanation += "Based on the code, this appears to be "
        if len(references) > 0:
            if any("class" in ref['context'].lower() for ref in references):
                explanation += f"a class that handles {topic} functionality."
            elif any("function" in ref['context'].lower() or "def" in ref['context'].lower()):
                explanation += f"a function or method related to {topic}."
            else:
                explanation += f"code related to {topic}."
        
        return {
            'answer': explanation,
            'references': references
        }

    def get_file_content(self, file_path):
        """Get content of a file from the loaded file contents"""
        if file_path in self.file_contents:
            return self.file_contents[file_path]
        
        # If not in memory, try to find a matching file
        for path in self.file_contents:
            if path.endswith(file_path) or file_path.endswith(path):
                return self.file_contents[path]
        
        return None

    def _answer_compare(self, match, question):
        """Handle 'compare X and Y' questions"""
        subject1 = match.group(1).strip()
        subject2 = match.group(2).strip()
        
        # Find the elements to compare
        elements1 = self._find_code_elements(subject1)
        elements2 = self._find_code_elements(subject2)
        
        if not elements1 or not elements2:
            return {
                'answer': f"I couldn't find enough information to compare '{subject1}' and '{subject2}'.",
                'references': []
            }
        
        # Determine what types of elements we're comparing
        type1 = elements1[0]['type']
        type2 = elements2[0]['type']
        
        if type1 != type2:
            return {
                'answer': f"Cannot compare {subject1} ({type1}) with {subject2} ({type2}) as they are different types.",
                'references': [
                    {'file': elements1[0]['file'], 'line': elements1[0]['line'], 'context': elements1[0].get('context', '')},
                    {'file': elements2[0]['file'], 'line': elements2[0]['line'], 'context': elements2[0].get('context', '')}
                ]
            }
        
        # Compare based on element type
        if type1 == 'function':
            comparison = self._compare_functions(elements1[0], elements2[0])
        elif type1 == 'class':
            comparison = self._compare_classes(elements1[0], elements2[0])
        elif type1 == 'file':
            comparison = self._compare_files(elements1[0]['file'], elements2[0]['file'])
        else:
            comparison = f"Both '{subject1}' and '{subject2}' are {type1}s, but I cannot provide a detailed comparison."
        
        return {
            'answer': comparison,
            'references': [
                {'file': elements1[0]['file'], 'line': elements1[0]['line'], 'context': elements1[0].get('context', '')},
                {'file': elements2[0]['file'], 'line': elements2[0]['line'], 'context': elements2[0].get('context', '')}
            ]
        }

    def _describe_concept(self, subject):
        """Describe a concept based on the code"""
        # Look for mentions of the concept in the code
        mentions = []
        for file_path, content in self.file_contents.items():
            if subject.lower() in content.lower():
                # Find the lines where the concept is mentioned
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if subject.lower() in line.lower():
                        context_start = max(0, i - 3)
                        context_end = min(len(lines), i + 3)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        mentions.append({
                            'file': file_path,
                            'line': i + 1,
                            'context': context
                        })
                        break  # Just find the first mention per file
        
        if not mentions:
            return {
                'answer': f"I couldn't find any information about '{subject}' in the code.",
                'references': []
            }
        
        # Generate a description based on the mentions
        description = f"Based on the code, '{subject}' appears to be "
        
        # Look for clues in the context
        if any("class" in mention['context'] for mention in mentions):
            description += f"a class or object that "
            if any("def __init__" in mention['context'] for mention in mentions):
                description += "initializes with some parameters and "
        elif any("def " + subject in mention['context'] for mention in mentions):
            description += f"a function that "
        elif any("import" in mention['context'] and subject in mention['context'] for mention in mentions):
            description += f"a module or library that "
        elif any("=" in mention['context'] and subject in mention['context'].split("=")[0] for mention in mentions):
            description += f"a variable that stores "
        else:
            description += f"a concept related to "
        
        description += f"is used in the project for functionality related to {subject}."
        
        return {
            'answer': description,
            'references': mentions[:3]  # Limit to 3 references
        }