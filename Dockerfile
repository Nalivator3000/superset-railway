FROM apache/superset:latest

# Копируем скрипт инициализации
COPY superset_init.sh /app/superset_init.sh
RUN chmod +x /app/superset_init.sh

# Устанавливаем рабочую директорию
WORKDIR /app

# Экспонируем порт
EXPOSE 8088

# Запускаем инициализацию и сервер
CMD ["/app/superset_init.sh"]
