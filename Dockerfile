FROM apache/superset:latest

# Switch to root to install packages
USER root

# Copy requirements and install
COPY requirements-local.txt /app/requirements-local.txt
RUN pip install --no-cache-dir -r /app/requirements-local.txt

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

# Экспонируем порт (Railway обычно использует 8080)
EXPOSE 8080

# Запускаем инициализацию и сервер
CMD ["/app/superset_init.sh"]
