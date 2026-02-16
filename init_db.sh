#!/bin/bash

echo "Waiting for database to be ready..."
sleep 5

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Database initialized successfully!"

