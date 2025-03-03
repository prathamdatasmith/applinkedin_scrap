import os

def create_project_structure():
    directories = [
        "src",
        "src/scraper",
        "src/utils",
        "src/config",
        "src/tests",
        "src/data",
        "src/logs"
    ]
    files = [
        "src/main.py",
        "src/scraper/__init__.py",
        "src/scraper/job_scraper.py",
        "src/scraper/description_extractor.py",
        "src/scraper/tech_stack_extractor.py",
        "src/utils/__init__.py",
        "src/utils/file_writer.py",
        "src/utils/request_handler.py",
        "src/config/settings.yaml",
        "src/config/tech_keywords.yaml",
        "src/tests/test_scraper.py",
        "src/tests/test_description_extractor.py",
        "src/tests/test_tech_stack_extractor.py",
        "src/data/job_listings.csv",
        "src/logs/scraper.log",
        "src/requirements.txt",
        "src/README.md"
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Create files
    for file in files:
        if not os.path.exists(file):
            with open(file, "w") as f:
                pass  # Create empty file
    
    print("Project structure created successfully!")

if __name__ == "__main__":
    create_project_structure()
