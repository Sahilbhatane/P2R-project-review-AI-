import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiAnalyzer:
    """Integration with Google's Gemini AI for code analysis"""
    
    def __init__(self):
        """Initialize the Gemini integration"""
        # Load API key from .env file or environment variables
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Gemini analysis will not work.")
            self.enabled = False
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.enabled = True
    
    def analyze_code(self, file_path, content):
        """Analyze code content using Gemini AI"""
        if not self.enabled:
            return self._get_default_analysis()
            
        try:
            prompt = f"""
            As a professional code analyzer, analyze the following code and provide:
            1. A quality score between 0-100
            2. List of code smells with severity (high/medium/low)
            3. Security issues if any
            4. Improvement suggestions with priority (high/medium/low)
            
            Respond in JSON format with these keys: quality_score, code_smells, security_issues, improvement_suggestions
            
            File: {file_path}
            
            ```
            {content}
            ```
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the response - assuming it's JSON-like content
            try:
                # Extract JSON from the response text
                import re
                import json
                
                text = response.text
                # Find JSON content between triple backticks if present
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = text
                
                # Clean up the string to make it valid JSON
                json_str = re.sub(r'[\n\r\t]', ' ', json_str)
                json_str = re.sub(r'```.*?```', '', json_str, flags=re.DOTALL)
                
                # Parse the JSON
                analysis = json.loads(json_str)
                
                # Ensure all expected keys exist
                if 'quality_score' not in analysis:
                    analysis['quality_score'] = 70
                if 'code_smells' not in analysis:
                    analysis['code_smells'] = []
                if 'security_issues' not in analysis:
                    analysis['security_issues'] = []
                if 'improvement_suggestions' not in analysis:
                    analysis['improvement_suggestions'] = []
                    
                return analysis
                
            except Exception as e:
                print(f"Error parsing Gemini response: {str(e)}")
                return self._get_default_analysis()
                
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self):
        """Return a default analysis when Gemini is not available"""
        return {
            'quality_score': 70,
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
