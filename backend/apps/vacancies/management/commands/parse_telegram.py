from django.core.management.base import BaseCommand
from apps.vacancies.tasks import parse_telegram_vacancies


class Command(BaseCommand):
    help = 'Ручной запуск парсинга Telegram-каналов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            choices=['python', 'devops', 'kyrgyzstan', 'frontend', 'remote', 'general'],
            default=None,
            help='Категория каналов для парсинга'
        )

        parser.add_argument(
            '--async',
            action='store_true',
            help='Запустить парсинг асинхронно через Celery',
        )

    def handle(self, *args, **options):
        category = options['category']
        is_async = options['async']

        # Заголовок
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 50))

        if category:
            self.stdout.write(self.style.SUCCESS(f'📱 Запуск парсинга Telegram ({category})'))
        else:
            self.stdout.write(self.style.SUCCESS('📱 Запуск парсинга ВСЕХ Telegram-каналов'))

        self.stdout.write(self.style.SUCCESS('═' * 50))
        self.stdout.write('')

        if is_async:
            task = parse_telegram_vacancies.delay(category=category)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Telegram задача запущена в фоне')
            )
            self.stdout.write(f'   Task ID: {task.id}')
        else:
            try:
                result = parse_telegram_vacancies(category=category)
                self._print_result(result)
            except Exception as e:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR('═' * 50))
                self.stdout.write(self.style.ERROR('❌ ОШИБКА'))
                self.stdout.write(self.style.ERROR('═' * 50))
                self.stdout.write(self.style.ERROR(f'{str(e)}'))
                self.stdout.write('')

    def _print_result(self, result: dict):
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f'✅ [TELEGRAM] Парсинг завершен успешно'))
            self.stdout.write(self.style.SUCCESS('─' * 50))
            self.stdout.write(f'   📦 Всего найдено:  {result.get("total", 0)}')
            self.stdout.write(f'   ➕ Новых:         {result.get("new", 0)}')
            self.stdout.write(f'   🔄 Обновлено:     {result.get("updated", 0)}')
        elif result.get('status') == 'no_vacancies':
            self.stdout.write(
                self.style.WARNING(f'⚠️  [TELEGRAM] Вакансий не найдено')
            )
        else:
            error = result.get('error', 'Неизвестная ошибка')
            self.stdout.write(self.style.ERROR(f'❌ [TELEGRAM] Ошибка парсинга'))
            self.stdout.write(self.style.ERROR('─' * 50))
            self.stdout.write(self.style.ERROR(f'   {error}'))