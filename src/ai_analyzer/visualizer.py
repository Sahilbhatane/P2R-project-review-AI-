import os
import re
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict

class CodeVisualizer:
    """Visualization module for code analysis"""
    
    def __init__(self):
        """Initialize the code visualizer"""
        self.fig_size = (10, 7)
        self.output_format = 'png'
        
    def generate_dependency_graph(self, file_analyses):
        """
        Generate a visualization of dependencies between files
        Returns a base64 encoded image
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Map of file paths to node names (use basename for clarity)
        node_names = {}
        for analysis in file_analyses:
            path = analysis['path']
            node_names[path] = os.path.basename(path)
            G.add_node(path)
            
        # Add edges for imports
        for analysis in file_analyses:
            source = analysis['path']
            if 'imports' in analysis:
                for imp in analysis['imports']:
                    # Simple heuristic to match imports to files
                    for target in node_names:
                        # Check if import likely refers to this file
                        if self._match_import_to_file(imp, target):
                            G.add_edge(source, target)
        
        # Generate the visualization
        plt.figure(figsize=self.fig_size)
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=False, node_size=700, node_color='skyblue', font_size=10, arrows=True)
        
        # Draw node labels
        nx.draw_networkx_labels(G, pos, labels=node_names)
        
        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format=self.output_format)
        img_data.seek(0)
        
        # Encode image to base64
        encoded = base64.b64encode(img_data.read()).decode('utf-8')
        plt.close()
        
        return encoded
    
    def generate_class_diagram(self, file_analyses):
        """
        Generate a simple class diagram from Python code
        Returns a base64 encoded image
        """
        # Create directed graph for classes
        G = nx.DiGraph()
        
        # Collect all classes
        classes = {}
        class_methods = defaultdict(list)
        inheritance = {}
        
        for analysis in file_analyses:
            if 'classes' not in analysis:
                continue
                
            for cls in analysis.get('classes', []):
                if isinstance(cls, dict) and 'name' in cls:
                    class_name = cls['name']
                    classes[class_name] = analysis['path']
                    
                    # Store inheritance relationships
                    if 'bases' in cls and cls['bases']:
                        inheritance[class_name] = cls['bases']
                    
                    # Store methods
                    if 'methods' in cls:
                        for method in cls['methods']:
                            if isinstance(method, dict) and 'name' in method:
                                class_methods[class_name].append(method['name'])
        
        # Add nodes for each class
        for class_name in classes:
            G.add_node(class_name)
            
        # Add inheritance edges
        for child, parents in inheritance.items():
            for parent in parents:
                if parent in classes:
                    G.add_edge(child, parent)
        
        # Generate the visualization
        plt.figure(figsize=self.fig_size)
        pos = nx.spring_layout(G)
        
        # Draw the graph
        nx.draw(G, pos, with_labels=True, node_size=2000, node_color='lightgreen', 
                font_size=10, font_weight='bold', arrows=True)
        
        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format=self.output_format)
        img_data.seek(0)
        
        # Encode image to base64
        encoded = base64.b64encode(img_data.read()).decode('utf-8')
        plt.close()
        
        return encoded
    
    def generate_complexity_chart(self, file_analyses):
        """
        Generate a bar chart showing complexity by file
        Returns a base64 encoded image
        """
        # Extract data
        files = []
        complexities = []
        
        for analysis in file_analyses:
            if 'ai_insights' in analysis and 'complexity' in analysis['ai_insights']:
                files.append(os.path.basename(analysis['path']))
                complexities.append(analysis['ai_insights']['complexity']['cyclomatic'])
        
        # Sort by complexity (descending)
        sorted_data = sorted(zip(files, complexities), key=lambda x: x[1], reverse=True)
        if not sorted_data:
            return None
            
        files, complexities = zip(*sorted_data)
        
        # Limit to top 15 files for readability
        if len(files) > 15:
            files = files[:15]
            complexities = complexities[:15]
        
        # Create the chart
        plt.figure(figsize=self.fig_size)
        plt.barh(files, complexities, color='coral')
        plt.xlabel('Cyclomatic Complexity')
        plt.ylabel('File')
        plt.title('Code Complexity by File')
        plt.tight_layout()
        
        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format=self.output_format)
        img_data.seek(0)
        
        # Encode image to base64
        encoded = base64.b64encode(img_data.read()).decode('utf-8')
        plt.close()
        
        return encoded
    
    def _match_import_to_file(self, import_str, file_path):
        """Heuristic to match import statements to files"""
        # Extract the imported module/package name
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
                
                # Check if the import refers to this file
                file_base = os.path.splitext(os.path.basename(file_path))[0]
                
                # Convert dot notation to path components
                imported_parts = imported.split('.')
                
                # Check for match
                if file_base == imported or file_base == imported_parts[-1]:
                    return True
                    
        return False
