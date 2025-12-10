import os

# Read SECRET_KEY from environment variable
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY')

# Debug: print what we got (will appear in logs)
print(f"DEBUG: SUPERSET_SECRET_KEY exists: {SECRET_KEY is not None}")
print(f"DEBUG: SECRET_KEY length: {len(SECRET_KEY) if SECRET_KEY else 0}")

# Fail if no SECRET_KEY is set
if not SECRET_KEY:
    raise ValueError("SUPERSET_SECRET_KEY environment variable is not set!")

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:////app/superset.db')

# Disable CSRF for easier setup (optional, can be removed for production)
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Enable public role
PUBLIC_ROLE_LIKE = "Gamma"
