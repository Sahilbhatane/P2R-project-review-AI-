import os
from .ml_analyzer import AICodeAnalyzer
from .visualizer import CodeVisualizer
from .code_qa import CodeQA
from .project_review import ProjectReviewer
from .gemini_integration import GeminiAnalyzer

class AIIntegrator:
    """
    Integration class that combines all AI analysis features
    and integrates them with the existing code analyzer
    """
    
    def __init__(self, code_analyzer=None):
        """Initialize the AI integrator with all components"""
        self.code_analyzer = code_analyzer
        self.ai_analyzer = AICodeAnalyzer()
        self.visualizer = CodeVisualizer()
        self.code_qa = CodeQA()
        self.project_reviewer = ProjectReviewer(code_analyzer, self.ai_analyzer)
        self.file_contents = {}
        # Add Gemini analyzer
        self.gemini_analyzer = GeminiAnalyzer()
    
    def analyze_file(self, file_path, content):
        """
        Perform comprehensive analysis on a file
        Combines basic analysis with AI-enhanced insights
        """
        # Store file content for later use in QA
        self.file_contents[file_path] = content
        
        # Perform basic analysis using the original analyzer if available
        if self.code_analyzer:
            basic_analysis = self.code_analyzer.analyze_file(file_path, content)
        else:
            # Simple fallback if original analyzer isn't available
            basic_analysis = {
                'path': file_path,
                'language': os.path.splitext(file_path)[1].lstrip('.'),
                'size': len(content.encode('utf-8')),
                'elements': []
            }
        
        # Add AI-enhanced analysis
        ai_analysis = self.ai_analyzer.analyze_file(file_path, content)
        
        # Add Gemini analysis
        gemini_results = self.gemini_analyzer.analyze_code(file_path, content)
        
        # Create ai_insights if it doesn't exist
        if 'ai_insights' not in ai_analysis:
            ai_analysis['ai_insights'] = {}
            
        # Add Gemini results to ai_insights
        ai_analysis['ai_insights'].update(gemini_results)
        
        # Merge the analyses
        merged_analysis = {**basic_analysis, **ai_analysis}
        
        # Add the content for later use in file comparison
        merged_analysis['content'] = content
        
        return merged_analysis
    
    def generate_project_summary(self, file_analyses):
        """
        Generate a comprehensive project summary with AI insights
        """
        # Remove file contents before passing to the analyzers
        cleaned_analyses = []
        for analysis in file_analyses:
            cleaned = {k: v for k, v in analysis.items() if k != 'content'}
            cleaned_analyses.append(cleaned)
        
        # Generate basic summary if code_analyzer is available
        if self.code_analyzer:
            basic_summary = self.code_analyzer.generate_project_summary(cleaned_analyses)
        else:
            basic_summary = {}
        
        # Generate AI summary
        ai_summary = self.ai_analyzer.generate_project_summary(cleaned_analyses)
        
        # Generate code similarity analysis
        similarity = self.ai_analyzer.analyze_code_similarity(file_analyses)
        
        # Generate full project review
        full_review = self.project_reviewer.generate_full_review(cleaned_analyses)
        
        # Initialize the code QA system with the analyses
        self.code_qa.load_project_data(cleaned_analyses, self.file_contents)
        
        # Generate visualizations
        visualizations = {
            'dependency_graph': self.visualizer.generate_dependency_graph(cleaned_analyses),
            'class_diagram': self.visualizer.generate_class_diagram(cleaned_analyses),
            'complexity_chart': self.visualizer.generate_complexity_chart(cleaned_analyses)
        }
        
        # Combine all insights
        combined_summary = {
            **basic_summary,
            'ai_summary': ai_summary.get('ai_summary', {}),
            'similarity_analysis': similarity,
            'full_review': full_review,
            'visualizations': visualizations
        }
        
        return combined_summary
    
    def answer_question(self, question):
        """
        Answer a question about the code using the QA system
        """
        return self.code_qa.answer_question(question)
