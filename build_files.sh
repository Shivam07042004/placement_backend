#!/bin/bash

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip --break-system-packages
pip install -r requirements.txt --break-system-packages

# Wait a moment for installation to complete
sleep 2

# Set the Django settings module
export DJANGO_SETTINGS_MODULE=placement_django_backend.settings

# Run Django management commands
echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build completed successfully!"