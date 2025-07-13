import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class GeminiAnalyzer:
    """Integration with Hugging Face Transformers for code analysis"""
    def __init__(self):
        # Use StarCoder or CodeBERT from Hugging Face
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("bigcode/starcoder")
            self.model = AutoModelForCausalLM.from_pretrained("bigcode/starcoder")
            self.enabled = True
        except Exception as e:
            print(f"Error loading StarCoder model: {str(e)}")
            self.enabled = False
    
    def analyze_code(self, file_path, content):
        """Analyze code content using StarCoder (Hugging Face)"""
        if not self.enabled:
            return self._get_default_analysis()
        try:
            prompt = f"""
            # Code Review
            # File: {file_path}
            # Please analyze the following code and provide:
            # 1. A quality score (0-100)
            # 2. List of code smells with severity (high/medium/low)
            # 3. Security issues
            # 4. Improvement suggestions
            # Respond in JSON format with keys: quality_score, code_smells, security_issues, improvement_suggestions
            {content}
            """
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            outputs = self.model.generate(**inputs, max_new_tokens=256)
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Try to extract JSON from the result
            import re, json
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    analysis = json.loads(json_str)
                    if 'quality_score' not in analysis:
                        analysis['quality_score'] = 70
                    if 'code_smells' not in analysis:
                        analysis['code_smells'] = []
                    if 'security_issues' not in analysis:
                        analysis['security_issues'] = []
                    if 'improvement_suggestions' not in analysis:
                        analysis['improvement_suggestions'] = []
                    return analysis
                except Exception:
                    pass
            return self._get_default_analysis()
        except Exception as e:
            print(f"Error calling StarCoder: {str(e)}")
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
