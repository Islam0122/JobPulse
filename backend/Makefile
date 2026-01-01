.PHONY: help install migrate run test clean docker-build docker-up docker-down setup dev redis celery beat

RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m

help:
	@echo "${BLUE}════════════════════════════════════════════════════════${NC}"
	@echo "${GREEN}           JobPulse Django Project${NC}"
	@echo "${BLUE}════════════════════════════════════════════════════════${NC}"
	@echo ""
	@echo "${YELLOW}📦 Установка и настройка:${NC}"
	@echo "  ${GREEN}make setup${NC}          - 🚀 Полная установка проекта (одна кнопка)"
	@echo "  ${GREEN}make install${NC}        - Установка зависимостей"
	@echo "  ${GREEN}make migrate${NC}        - Выполнение миграций"
	@echo "  ${GREEN}make fixtures${NC}       - Загрузка тестовых данных"
	@echo ""
	@echo "${YELLOW}🏃 Запуск:${NC}"
	@echo "  ${GREEN}make dev${NC}            - 🎯 Запуск всех сервисов локально (Django+Redis+Celery)"
	@echo "  ${GREEN}make run${NC}            - Запуск Django сервера"
	@echo "  ${GREEN}make redis${NC}          - Запуск Redis сервера"
	@echo "  ${GREEN}make celery${NC}         - Запуск Celery worker"
	@echo "  ${GREEN}make beat${NC}           - Запуск Celery beat"
	@echo ""
	@echo "${YELLOW}🐳 Docker команды:${NC}"
	@echo "  ${GREEN}make docker-setup${NC}   - 🚀 Запуск проекта в Docker (одна кнопка)"
	@echo "  ${GREEN}make docker-build${NC}   - Сборка Docker образов"
	@echo "  ${GREEN}make docker-up${NC}      - Запуск всех контейнеров"
	@echo "  ${GREEN}make docker-down${NC}    - Остановка контейнеров"
	@echo "  ${GREEN}make docker-logs${NC}    - Просмотр логов"
	@echo "  ${GREEN}make docker-restart${NC} - Перезапуск контейнеров"
	@echo ""
	@echo "${YELLOW}🧪 Тестирование и проверка:${NC}"
	@echo "  ${GREEN}make test${NC}           - Запуск тестов"
	@echo "  ${GREEN}make test-redis${NC}     - Проверка работы Redis"
	@echo "  ${GREEN}make check${NC}          - Проверка настройки проекта"
	@echo ""
	@echo "${YELLOW}🗄️ База данных:${NC}"
	@echo "  ${GREEN}make superuser${NC}      - Создать суперпользователя"
	@echo "  ${GREEN}make shell${NC}          - Django shell"
	@echo "  ${GREEN}make dbshell${NC}        - Database shell"
	@echo ""
	@echo "${YELLOW}🧹 Очистка:${NC}"
	@echo "  ${GREEN}make clean${NC}          - Очистка временных файлов"
	@echo "  ${GREEN}make clean-all${NC}      - Полная очистка (включая БД и кэш)"
	@echo ""
	@echo "${BLUE}════════════════════════════════════════════════════════${NC}"

setup: check-env
	@echo "${GREEN}🚀 Начинаем полную настройку проекта...${NC}"
	@$(MAKE) install
	@$(MAKE) create-env
	@$(MAKE) migrate
	@$(MAKE) create-test-data
	@$(MAKE) collectstatic
	@echo ""
	@echo "${GREEN}════════════════════════════════════════════════════════${NC}"
	@echo "${GREEN}✅ Проект успешно настроен!${NC}"
	@echo "${GREEN}════════════════════════════════════════════════════════${NC}"
	@echo ""
	@echo "${YELLOW}📋 Тестовые пользователи:${NC}"
	@echo "   Telegram ID: 123456789 - john_doe (Backend Developer)"
	@echo "   Telegram ID: 987654321 - jane_smith (Frontend Developer)"
	@echo "   Telegram ID: 555555555 - alex_tech (Full Stack Developer)"
	@echo ""
	@echo "${YELLOW}🌐 Для запуска локально:${NC}"
	@echo "   ${GREEN}make dev${NC} - запустит Django, Redis, Celery"
	@echo ""
	@echo "${YELLOW}🐳 Для запуска в Docker:${NC}"
	@echo "   ${GREEN}make docker-setup${NC}"
	@echo ""
	@echo "${YELLOW}📚 API документация будет доступна:${NC}"
	@echo "   http://localhost:8000/api/swagger/"
	@echo "   http://localhost:8000/admin/"
	@echo ""


dev:
	@echo "${GREEN}🎯 Запуск всех сервисов локально...${NC}"
	@echo "${YELLOW}Открываю 4 терминала:${NC}"
	@echo "  1. Django Server"
	@echo "  2. Redis Server"
	@echo "  3. Celery Worker"
	@echo "  4. Celery Beat"
	@echo ""
	@if command -v gnome-terminal > /dev/null; then \
		gnome-terminal --tab --title="Django" -- bash -c "cd $(PWD) && source venv/bin/activate && python manage.py runserver; exec bash" & \
		sleep 1; \
		gnome-terminal --tab --title="Redis" -- bash -c "redis-server; exec bash" & \
		sleep 2; \
		gnome-terminal --tab --title="Celery Worker" -- bash -c "cd $(PWD) && source venv/bin/activate && celery -A config worker -l info; exec bash" & \
		gnome-terminal --tab --title="Celery Beat" -- bash -c "cd $(PWD) && source venv/bin/activate && celery -A config beat -l info; exec bash" & \
		echo "${GREEN}✅ Все сервисы запущены!${NC}"; \
	elif command -v osascript > /dev/null; then \
		osascript -e 'tell app "Terminal" to do script "cd $(PWD) && source venv/bin/activate && python manage.py runserver"' & \
		sleep 1; \
		osascript -e 'tell app "Terminal" to do script "redis-server"' & \
		sleep 2; \
		osascript -e 'tell app "Terminal" to do script "cd $(PWD) && source venv/bin/activate && celery -A config worker -l info"' & \
		osascript -e 'tell app "Terminal" to do script "cd $(PWD) && source venv/bin/activate && celery -A config beat -l info"' & \
		echo "${GREEN}✅ Все сервисы запущены!${NC}"; \
	else \
		echo "${RED}❌ Автоматический запуск недоступен${NC}"; \
		echo "${YELLOW}Запустите вручную в отдельных терминалах:${NC}"; \
		echo "  Terminal 1: ${GREEN}make run${NC}"; \
		echo "  Terminal 2: ${GREEN}make redis${NC}"; \
		echo "  Terminal 3: ${GREEN}make celery${NC}"; \
		echo "  Terminal 4: ${GREEN}make beat${NC}"; \
	fi


docker-setup:
	@echo "${GREEN}🐳 Запуск проекта в Docker...${NC}"
	@$(MAKE) docker-build
	@$(MAKE) docker-up
	@sleep 5
	@docker-compose exec web python manage.py migrate
	@docker-compose exec web python manage.py create_test_users
	@docker-compose exec web python manage.py collectstatic --noinput
	@echo ""
	@echo "${GREEN}════════════════════════════════════════════════════════${NC}"
	@echo "${GREEN}✅ Docker контейнеры запущены!${NC}"
	@echo "${GREEN}════════════════════════════════════════════════════════${NC}"
	@echo ""
	@echo "${YELLOW}🌐 Сервисы доступны:${NC}"
	@echo "   Django:     http://localhost:8000"
	@echo "   Swagger:    http://localhost:8000/api/swagger/"
	@echo "   Admin:      http://localhost:8000/admin/"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis:      localhost:6379"
	@echo ""
	@echo "${YELLOW}📊 Полезные команды:${NC}"
	@echo "   ${GREEN}make docker-logs${NC}    - Просмотр логов"
	@echo "   ${GREEN}make docker-down${NC}    - Остановить контейнеры"
	@echo "   ${GREEN}make docker-restart${NC} - Перезапустить"
	@echo ""

install:
	@echo "${GREEN}📦 Установка зависимостей...${NC}"
	@if [ ! -d "venv" ]; then \
		echo "${YELLOW}Создание виртуального окружения...${NC}"; \
		python3 -m venv venv; \
	fi
	@echo "${YELLOW}Активация venv и установка пакетов...${NC}"
	@. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "${GREEN}✅ Зависимости установлены${NC}"

create-env:
	@if [ ! -f ".env" ]; then \
		echo "${YELLOW}📝 Создание .env файла...${NC}"; \
		cp .env.example .env; \
		echo "${GREEN}✅ Создан .env файл${NC}"; \
		echo "${YELLOW}⚠️  Отредактируйте .env для продакшена!${NC}"; \
	else \
		echo "${BLUE}ℹ️  .env файл уже существует${NC}"; \
	fi

migrate:
	@echo "${GREEN}🗄️  Выполнение миграций...${NC}"
	@. venv/bin/activate && python manage.py makemigrations
	@. venv/bin/activate && python manage.py migrate
	@echo "${GREEN}✅ Миграции применены${NC}"

create-test-data:
	@echo "${GREEN}👥 Создание тестовых данных...${NC}"
	@. venv/bin/activate && python manage.py create_test_users
	@echo "${GREEN}✅ Тестовые данные созданы${NC}"

collectstatic:
	@echo "${GREEN}🎨 Сбор статических файлов...${NC}"
	@. venv/bin/activate && python manage.py collectstatic --noinput
	@echo "${GREEN}✅ Статика собрана${NC}"


run:
	@echo "${GREEN}🚀 Запуск Django сервера...${NC}"
	@. venv/bin/activate && python manage.py runserver

redis:
	@echo "${GREEN}🔴 Запуск Redis сервера...${NC}"
	@if command -v redis-server > /dev/null; then \
		redis-server; \
	else \
		echo "${RED}❌ Redis не установлен. Установите: brew install redis или apt install redis${NC}"; \
	fi

celery:
	@echo "${GREEN}🔄 Запуск Celery worker...${NC}"
	@. venv/bin/activate && celery -A config worker -l info

beat:
	@echo "${GREEN}⏰ Запуск Celery beat...${NC}"
	@. venv/bin/activate && celery -A config beat -l info

docker-build:
	@echo "${GREEN}🔨 Сборка Docker образов...${NC}"
	@docker-compose build
	@echo "${GREEN}✅ Образы собраны${NC}"

docker-up:
	@echo "${GREEN}⬆️  Запуск Docker контейнеров...${NC}"
	@docker-compose up -d
	@echo "${GREEN}✅ Контейнеры запущены${NC}"

docker-down:
	@echo "${YELLOW}⬇️  Остановка Docker контейнеров...${NC}"
	@docker-compose down
	@echo "${GREEN}✅ Контейнеры остановлены${NC}"

docker-restart:
	@echo "${YELLOW}🔄 Перезапуск Docker контейнеров...${NC}"
	@$(MAKE) docker-down
	@$(MAKE) docker-up
	@echo "${GREEN}✅ Контейнеры перезапущены${NC}"

docker-logs:
	@echo "${BLUE}📋 Просмотр логов (Ctrl+C для выхода)...${NC}"
	@docker-compose logs -f

docker-ps:
	@echo "${BLUE}📊 Статус контейнеров:${NC}"
	@docker-compose ps

test:
	@echo "${GREEN}🧪 Запуск тестов...${NC}"
	@. venv/bin/activate && pytest

test-redis:
	@echo "${GREEN}🔴 Проверка Redis...${NC}"
	@. venv/bin/activate && python manage.py test_redis

check:
	@echo "${BLUE}🔍 Проверка настройки проекта...${NC}"
	@. venv/bin/activate && python manage.py check
	@echo "${GREEN}✅ Проверка завершена${NC}"


superuser:
	@echo "${GREEN}👤 Создание суперпользователя...${NC}"
	@. venv/bin/activate && python manage.py createsuperuser

shell:
	@echo "${GREEN}🐚 Django shell...${NC}"
	@. venv/bin/activate && python manage.py shell

dbshell:
	@echo "${GREEN}🗄️  Database shell...${NC}"
	@. venv/bin/activate && python manage.py dbshell


clean:
	@echo "${YELLOW}🧹 Очистка временных файлов...${NC}"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf celerybeat-schedule 2>/dev/null || true
	@echo "${GREEN}✅ Очистка завершена${NC}"

clean-all: clean
	@echo "${RED}🧹 Полная очистка (БД, кэш, venv)...${NC}"
	@rm -rf db.sqlite3 2>/dev/null || true
	@rm -rf staticfiles 2>/dev/null || true
	@rm -rf media 2>/dev/null || true
	@echo "${YELLOW}⚠️  Для удаления venv выполните: rm -rf venv${NC}"
	@echo "${GREEN}✅ Полная очистка завершена${NC}"


check-env:
	@command -v python3 >/dev/null 2>&1 || { echo "${RED}❌ Python3 не установлен${NC}"; exit 1; }
	@command -v pip >/dev/null 2>&1 || { echo "${RED}❌ Pip не установлен${NC}"; exit 1; }
	@echo "${GREEN}✅ Python и Pip установлены${NC}"

requirements:
	@echo "${GREEN}📋 Создание requirements.txt...${NC}"
	@. venv/bin/activate && pip freeze > requirements.txt
	@echo "${GREEN}✅ requirements.txt обновлен${NC}"