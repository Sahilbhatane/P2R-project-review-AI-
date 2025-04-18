import os
import re
import shutil
import requests
import tempfile
import zipfile
from git import Repo

class GitHubRepo:
    def __init__(self, repo_url, project_dir):
        """
        Initialize with a GitHub repository URL and local directory
        """
        self.repo_url = repo_url
        self.project_dir = project_dir
        
        # Extract owner and repo name from URL
        url_pattern = r'github\.com[:/]([^/]+)/([^/]+)'
        match = re.search(url_pattern, repo_url)
        
        if match:
            self.owner = match.group(1)
            self.repo = match.group(2)
            # Remove .git extension if present
            self.repo = self.repo.replace('.git', '')
        else:
            raise ValueError("Invalid GitHub repository URL")
    
    def clone_repo(self):
        """
        Clone the repository to the local directory
        """
        # Try using Git clone first
        try:
            if os.path.exists(self.project_dir):
                shutil.rmtree(self.project_dir)
            
            os.makedirs(self.project_dir, exist_ok=True)
            
            Repo.clone_from(self.repo_url, self.project_dir)
            return True
        except Exception as e:
            print(f"Git clone failed: {str(e)}")
            # Fall back to downloading as ZIP
            return self._download_as_zip()
    
    def _download_as_zip(self):
        """
        Alternative method to download repository as a ZIP file
        """
        zip_url = f"https://github.com/{self.owner}/{self.repo}/archive/master.zip"
        alt_zip_url = f"https://github.com/{self.owner}/{self.repo}/archive/main.zip"
        
        temp_zip = os.path.join(tempfile.gettempdir(), f"{self.owner}_{self.repo}.zip")
        
        # Try master branch first, then main
        response = requests.get(zip_url, stream=True)
        if response.status_code != 200:
            response = requests.get(alt_zip_url, stream=True)
            if response.status_code != 200:
                raise ValueError("Could not download repository")
        
        # Save the zip file
        with open(temp_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        # Extract the zip file
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(self.project_dir))
            
            # Get the extracted folder name
            extracted_dir = zip_ref.namelist()[0].split('/')[0]
            extracted_path = os.path.join(os.path.dirname(self.project_dir), extracted_dir)
            
            # Move contents to project directory
            if os.path.exists(self.project_dir):
                shutil.rmtree(self.project_dir)
            
            shutil.move(extracted_path, self.project_dir)
        
        # Clean up
        os.remove(temp_zip)
        
        return True 