import sys
import os

# Set the path to your app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from flask_app import create_app

application = create_app()
