# Apache Superset on Railway

Apache Superset deployment for Railway platform.

## Deployment

1. Push this repository to GitHub
2. Create a new project on Railway
3. Deploy from GitHub repository
4. Set environment variables:
   - `SUPERSET_SECRET_KEY` - random secret key for security
   - `ADMIN_USERNAME` - admin username (default: admin)
   - `ADMIN_PASSWORD` - admin password (default: admin)
   - `ADMIN_EMAIL` - admin email (default: admin@superset.com)

## Access

After deployment, access Superset at your Railway URL on port 8088.

Login with the credentials you set in environment variables.
