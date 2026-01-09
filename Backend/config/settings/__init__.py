"""
Settings initialization for Sha8alny project.

Automatically loads the appropriate settings module based on DJANGO_SETTINGS_MODULE
environment variable or defaults to development settings.
"""

import os

# Get environment from DJANGO_SETTINGS_MODULE or default to development
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Extract environment name (development, production, etc.)
environment = settings_module.split('.')[-1]

# Import the appropriate settings
if environment == 'production':
    from .production import *
elif environment == 'development':
    from .development import *
else:
    # Default to development
    from .development import *
