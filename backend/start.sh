#!/bin/bash

echo "Starting application setup..."

# Run database migrations/setup
echo "Running database setup..."
python setup.py

# Wait for database to be ready (if using external DB)
echo "Waiting for database connection..."
python -c "
import sys
import time
from ticketflow.database.connection import db_manager

max_retries = 30
for i in range(max_retries):
    try:
        # Test database connection
        db_manager.connect()
        print('Database is ready!')
        break
    except Exception as e:
        if i < max_retries - 1:
            print(f'Database not ready, retrying in 2 seconds... ({i+1}/{max_retries})')
            time.sleep(2)
        else:
            print('Could not connect to database after 30 attempts')
            sys.exit(1)
"

# Run any additional setup
echo "Running additional setup tasks..."

echo "Setup completed, starting application..."
python run_api.py