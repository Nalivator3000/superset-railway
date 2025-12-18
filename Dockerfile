FROM apache/superset:latest

USER root

# Copy Superset configuration and initialization scripts
COPY superset_config.py /app/superset_config.py
COPY superset_init.py /app/superset_init.py
COPY superset-entrypoint.sh /app/superset-entrypoint.sh

# Ensure entrypoint is executable
RUN chmod +x /app/superset-entrypoint.sh

# Superset configuration path
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Expose Superset port
EXPOSE 8088

# Use custom entrypoint that installs psycopg2 and runs Superset
ENTRYPOINT ["/bin/bash", "/app/superset-entrypoint.sh"]
