import os

# Read SECRET_KEY from environment variable
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'CHANGE_ME_TO_A_COMPLEX_RANDOM_SECRET')

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:////app/superset.db')

# Disable CSRF for easier setup (optional, can be removed for production)
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Enable public role
PUBLIC_ROLE_LIKE = "Gamma"
