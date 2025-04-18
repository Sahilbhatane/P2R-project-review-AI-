#!/usr/bin/env python3
"""
Test script for the code analyzer in the P2R project.
This script analyzes a sample Python file to verify that the code analyzer works correctly.
"""

import os
import json
from src.code_analyzer.analyzer import CodeAnalyzer
from src.utils.file_utils import read_file_content

def test_analyzer():
    """Test the code analyzer with a sample Python file"""
    # Create a sample Python file
    sample_code = """
import os
import sys
from datetime import datetime

# A simple class
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old."
    
    def is_adult(self):
        return self.age >= 18

# A simple function
def calculate_age(birth_year):
    current_year = datetime.now().year
    return current_year - birth_year

# Main code
if __name__ == "__main__":
    person = Person("John Doe", 30)
    print(person.greet())
    
    # Calculate age for different birth years
    years = [1990, 2000, 2010]
    for year in years:
        age = calculate_age(year)
        print(f"Someone born in {year} is {age} years old.")
"""

    # Create a temporary file
    with open("sample_code.py", "w") as f:
        f.write(sample_code)
    
    try:
        # Initialize the analyzer
        analyzer = CodeAnalyzer()
        
        # Read the file content
        file_content = read_file_content("sample_code.py")
        
        # Analyze the file
        analysis = analyzer.analyze_file("sample_code.py", file_content)
        
        # Print the analysis results
        print("\n=== SAMPLE CODE ANALYSIS ===\n")
        print(f"File: {analysis['path']}")
        print(f"Language: {analysis['language']}")
        print(f"Summary: {analysis['summary']}")
        print(f"Lines: {analysis['line_count']}")
        print(f"Comments: {analysis['comment_count']} ({int(analysis['comment_ratio'] * 100)}%)")
        
        print("\nClasses:")
        for cls in analysis.get('classes', []):
            print(f"- {cls}")
        
        print("\nFunctions:")
        for func in analysis.get('functions', []):
            print(f"- {func}")
        
        print("\nImports:")
        for imp in analysis.get('imports', []):
            print(f"- {imp}")
        
        print("\nElements:")
        for elem in analysis.get('elements', []):
            print(f"- {elem['type']}: {elem['name']} (line {elem['line']})")
        
        print("\n=== RAW ANALYSIS DATA ===\n")
        print(json.dumps(analysis, indent=2))
        
        # Test project summary
        project_summary = analyzer.generate_project_summary([analysis])
        
        print("\n=== PROJECT SUMMARY ===\n")
        print(f"Text: {project_summary['text']}")
        print(f"File count: {project_summary['file_count']}")
        print(f"Total lines: {project_summary['total_lines']}")
        print(f"Main languages: {project_summary['main_languages']}")
        print(f"Class count: {project_summary['class_count']}")
        print(f"Function count: {project_summary['function_count']}")
        
        print("\nCommon imports:")
        for imp, count in project_summary['common_imports']:
            print(f"- {imp}: {count}")
        
        return True
    finally:
        # Clean up the temporary file
        if os.path.exists("sample_code.py"):
            os.remove("sample_code.py")

if __name__ == "__main__":
    if test_analyzer():
        print("\n✅ Analyzer test completed successfully!")
    else:
        print("\n❌ Analyzer test failed!") 