# Project-to-Review (P2R)

A Python application that helps you understand codebases by analyzing and generating structured summaries of each file and providing a comprehensive project review.

## Features

- Upload files or link to a GitHub repository
- Automatically process and analyze each file
- Generate readable summaries of functions, imports, and code structure
- Implement custom code analysis algorithms to extract key information
- Provide a comprehensive project review
- User-friendly interface for reviewing analysis results

## How It Works

P2R uses Python's built-in analysis capabilities, like the Abstract Syntax Tree (AST) module, to analyze code files. It doesn't rely on external AI APIs but instead implements custom code analysis algorithms to extract meaningful information from your codebase.

The analysis includes:
- Detecting and categorizing code elements (classes, functions, imports, etc.)
- Calculating code metrics (lines of code, comment ratio, etc.)
- Generating summaries based on structural analysis
- Providing a comprehensive project overview

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/p2r.git
   cd p2r
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the application:
   ```
   python main.py
   ```

4. Access the web interface at http://localhost:5000

## Usage

1. **Upload Files**: Drag and drop files or select them from your file system
2. **GitHub Repository**: Enter the URL of a public GitHub repository
3. **Review Results**: Browse through the analyzed files and project summary

## Project Structure

- `main.py`: Main application entry point
- `src/code_analyzer/`: Code analysis modules
- `src/github_handler/`: GitHub repository integration
- `src/utils/`: Utility functions and helpers
- `templates/`: HTML templates for the web interface
- `static/`: Static assets (CSS, JavaScript)

## How to Extend

### Adding Support for New Languages

To add support for a new programming language, you can create a new analyzer in the `src/code_analyzer/analyzer.py` file:

1. Add the language to the `language_analyzers` dictionary
2. Create an analysis function (e.g., `_analyze_ruby`)
3. Implement language-specific parsing and structure extraction
4. Return the extracted information in the standard format

### Customizing the Analysis

You can enhance the analysis by:
- Adding more code metrics
- Implementing more sophisticated code pattern recognition
- Extending the summary generation with additional insights
- Adding visualization options for code structure

## Technologies

- Python
- Flask (web framework)
- Git integration
- AST (Abstract Syntax Tree) for code analysis
- Custom code summarization algorithms 