FROM apache/superset:latest

# Switch to root to install packages
USER root

# Install PostgreSQL driver and other database drivers
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy-redshift \
    mysqlclient \
    cx_Oracle

# Копируем скрипт инициализации
COPY superset_init.sh /app/superset_init.sh
RUN chmod +x /app/superset_init.sh

# Switch back to superset user
USER superset

# Устанавливаем рабочую директорию
WORKDIR /app

# Экспонируем порт
EXPOSE 8088

# Запускаем инициализацию и сервер
CMD ["/app/superset_init.sh"]
