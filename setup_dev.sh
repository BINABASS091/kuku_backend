#!/bin/bash

# Exit on error
set -e

# Copy development environment file
if [ ! -f .env ]; then
    cp .env.development .env
    echo "Copied .env.development to .env"
else
    echo ".env file already exists, skipping..."
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating and activating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py createsuperuser --noinput --username=admin --email=admin@example.com || true

# Set a default password for the superuser
echo "Setting superuser password..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='admin')
    user.set_password('admin')
    user.save()
    print('Superuser created/updated successfully')
except Exception as e:
    print(f'Error creating/updating superuser: {e}'
"

echo "\nDevelopment setup complete!"
echo "To start the development server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo "\nAdmin credentials:"
echo "  Username: admin"
echo "  Password: admin"
