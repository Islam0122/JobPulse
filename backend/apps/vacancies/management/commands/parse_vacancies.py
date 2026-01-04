from django.core.management.base import BaseCommand
from apps.vacancies.tasks import parse_hh_vacancies


class Command(BaseCommand):
    help = 'Ручной запуск парсинга вакансий с HH.ru'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Запустить парсинг асинхронно через Celery',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Запуск парсинга вакансий...'))
        self.stdout.write('')

        if options['async']:
            task = parse_hh_vacancies.delay()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Парсинг запущен в фоне (Task ID: {task.id})')
            )
            self.stdout.write('')
            self.stdout.write('Для просмотра статуса проверьте:')
            self.stdout.write('  - Админку: /admin/vacancies/parsinglog/')
            self.stdout.write('  - Celery логи')
        else:
            result = parse_hh_vacancies()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('════════════════════════════════════════'))
            self.stdout.write(self.style.SUCCESS('✅ Парсинг завершен!'))
            self.stdout.write(self.style.SUCCESS('════════════════════════════════════════'))
            self.stdout.write('')
            self.stdout.write(f"📊 Статистика:")
            self.stdout.write(f"   Всего найдено: {result.get('total', 0)}")
            self.stdout.write(f"   Новых: {result.get('new', 0)}")
            self.stdout.write(f"   Обновлено: {result.get('updated', 0)}")
            self.stdout.write('')