import sys
import os

# Add your application directory to the Python path
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'trivia-cards', '3.9', 'bin', 'python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask app
from app import app as application

# cPanel uses 'application' not 'app'
