FROM apache/superset:latest-dev

# Switch to root
USER root

# Копируем конфигурацию и скрипт
COPY superset_config.py /app/superset_config.py
COPY superset_init.sh /app/superset_init.sh
RUN chmod +x /app/superset_init.sh

# Устанавливаем путь к конфигу
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Switch back to superset user
USER superset

WORKDIR /app
EXPOSE 8080

CMD ["/app/superset_init.sh"]
