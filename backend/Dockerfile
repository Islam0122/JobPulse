# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY ../C26_AccessControlSystem_26_project/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY ../C26_AccessControlSystem_26_project .

# Создаём директорию для статики
RUN mkdir -p /app/staticfiles

# Команда по умолчанию
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
