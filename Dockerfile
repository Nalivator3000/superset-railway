FROM apache/superset:latest

# Switch to root to install packages
USER root

# Install PostgreSQL driver
RUN pip install --no-cache-dir psycopg2-binary

# Копируем конфигурацию и скрипт инициализации
COPY superset_config.py /app/superset_config.py
COPY superset_init.sh /app/superset_init.sh
RUN chmod +x /app/superset_init.sh

# Устанавливаем путь к конфигу
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Switch back to superset user
USER superset

# Устанавливаем рабочую директорию
WORKDIR /app

# Экспонируем порт
EXPOSE 8088

# Запускаем инициализацию и сервер
CMD ["/app/superset_init.sh"]
