import os

# Read SECRET_KEY from environment variable or use hardcoded fallback
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'gU484SWDdzlHawI3F5E0NywcX7zuLkC6Lf4V/fPVUdWut2mmvXJL/OJQ')

# Debug: print what we got (will appear in logs)
print(f"DEBUG: SECRET_KEY source: {'env' if os.environ.get('SUPERSET_SECRET_KEY') else 'hardcoded'}")
print(f"DEBUG: SECRET_KEY length: {len(SECRET_KEY)}")

# Database configuration - use in-memory SQLite for Superset metadata
# Note: This means metadata will be lost on restart, but it's ok for Railway
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/superset.db'

# Disable CSRF for easier setup (optional, can be removed for production)
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Enable public role
PUBLIC_ROLE_LIKE = "Gamma"
