#!/home/username/virtualenv/trivia-cards/bin/python3
# -*- coding: utf-8 -*-

import sys
import os

# Add your application to the path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)
