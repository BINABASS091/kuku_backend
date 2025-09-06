#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Set the default settings module to config.settings
    # This will automatically use development settings unless DJANGO_ENV is set to 'production'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Load environment variables from .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    # Add the project directory to the Python path
    project_path = os.path.dirname(os.path.abspath(__file__))
    if project_path not in sys.path:
        sys.path.append(project_path)
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
