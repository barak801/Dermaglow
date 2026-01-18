import os
import sys

# Set up the path to the virtual environment if necessary
# sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

# In cPanel/Passenger, the variable 'application' is the WSGI entry point
if __name__ == "__main__":
    application.run()
