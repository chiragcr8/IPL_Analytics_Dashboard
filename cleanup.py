import os
import shutil

ESSENTIAL_FILES = {
    'app.py',
    'requirements.txt',
    'start.bat',
    'matches.csv',
    'deliveries.csv',
    'static/style.css',
    '.streamlit/config.toml',
    'README.md',
    '.gitignore',
    'venv'
}

def is_essential(path):
    # Check if the path or any of its parents are essential
    current = path
    while current:
        if current in ESSENTIAL_FILES:
            return True
        current = os.path.dirname(current)
    return False

def cleanup():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Walk through all files and directories
    for root, dirs, files in os.walk(base_dir, topdown=False):
        # Remove unwanted files
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            
            if not is_essential(rel_path):
                try:
                    os.remove(full_path)
                    print(f"Removed file: {rel_path}")
                except Exception as e:
                    print(f"Error removing {rel_path}: {e}")

        # Remove empty directories
        for dir_name in dirs:
            full_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(full_path, base_dir)
            
            if not is_essential(rel_path):
                try:
                    if not os.listdir(full_path):  # Check if directory is empty
                        os.rmdir(full_path)
                        print(f"Removed empty directory: {rel_path}")
                except Exception as e:
                    print(f"Error removing directory {rel_path}: {e}")

if __name__ == '__main__':
    cleanup()