from django.core.management.base import BaseCommand
from apps.vacancies.tasks import (
    parse_hh_vacancies,
    parse_devkg_vacancies,
    parse_all_sources
)


class Command(BaseCommand):
    help = 'Ручной запуск парсинга вакансий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['hh', 'devkg', 'all'],
            default='all',
            help='Источник для парсинга: hh (HH.ru), devkg (Dev.kg), all (все источники)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Запустить парсинг асинхронно через Celery',
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=3,
            help='Количество страниц для парсинга Dev.kg (по умолчанию 3)'
        )

    def handle(self, *args, **options):
        source = options['source']
        is_async = options['async']
        pages = options['pages']

        # Заголовок
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 50))
        if source == 'all':
            self.stdout.write(self.style.SUCCESS('🌐 Запуск парсинга ВСЕХ источников'))
        elif source == 'hh':
            self.stdout.write(self.style.SUCCESS('🚀 Запуск парсинга HH.ru'))
        else:
            self.stdout.write(self.style.SUCCESS(f'🚀 Запуск парсинга Dev.kg ({pages} страниц)'))
        self.stdout.write(self.style.SUCCESS('═' * 50))
        self.stdout.write('')

        if is_async:
            # Асинхронный запуск
            self._run_async(source, pages)
        else:
            # Синхронный запуск
            self._run_sync(source, pages)

    def _run_async(self, source: str, pages: int):
        """Асинхронный запуск через Celery"""
        if source == 'hh':
            task = parse_hh_vacancies.delay()
            self.stdout.write(
                self.style.SUCCESS(f'✅ HH.ru задача запущена в фоне')
            )
            self.stdout.write(f'   Task ID: {task.id}')

        elif source == 'devkg':
            task = parse_devkg_vacancies.delay(max_pages=pages)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Dev.kg задача запущена в фоне')
            )
            self.stdout.write(f'   Task ID: {task.id}')
            self.stdout.write(f'   Страниц: {pages}')

        else:
            task = parse_all_sources.delay()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Задача парсинга всех источников запущена в фоне')
            )
            self.stdout.write(f'   Task ID: {task.id}')

        self.stdout.write('')
        self.stdout.write('📊 Для просмотра статуса:')
        self.stdout.write('   • Админка: /admin/vacancies/parsinglog/')
        self.stdout.write('   • Celery логи')
        self.stdout.write('')

    def _run_sync(self, source: str, pages: int):
        """Синхронный запуск"""
        try:
            if source == 'hh':
                result = parse_hh_vacancies()
                self._print_result(result, 'HH.ru')

            elif source == 'devkg':
                result = parse_devkg_vacancies(max_pages=pages)
                self._print_result(result, 'Dev.kg')

            else:
                results = parse_all_sources()

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('═' * 50))
                self.stdout.write(self.style.SUCCESS('📊 РЕЗУЛЬТАТЫ ПО ВСЕМ ИСТОЧНИКАМ'))
                self.stdout.write(self.style.SUCCESS('═' * 50))

                for src, res in results.items():
                    self.stdout.write('')
                    self._print_result(res, src.upper())

                # Общая статистика
                total_new = sum(r.get('new', 0) for r in results.values() if isinstance(r, dict))
                total_updated = sum(r.get('updated', 0) for r in results.values() if isinstance(r, dict))
                total_found = sum(r.get('total', 0) for r in results.values() if isinstance(r, dict))

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('═' * 50))
                self.stdout.write(self.style.SUCCESS('📈 ИТОГО'))
                self.stdout.write(self.style.SUCCESS('═' * 50))
                self.stdout.write(f'   Всего найдено: {total_found}')
                self.stdout.write(f'   Новых: {total_new}')
                self.stdout.write(f'   Обновлено: {total_updated}')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('═' * 50))
            self.stdout.write(self.style.ERROR('❌ ОШИБКА'))
            self.stdout.write(self.style.ERROR('═' * 50))
            self.stdout.write(self.style.ERROR(f'{str(e)}'))
            self.stdout.write('')

    def _print_result(self, result: dict, source_name: str):
        """Красивый вывод результатов"""
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f'✅ [{source_name}] Парсинг завершен успешно'))
            self.stdout.write(self.style.SUCCESS('─' * 50))
            self.stdout.write(f'   📦 Всего найдено:  {result.get("total", 0)}')
            self.stdout.write(f'   ➕ Новых:         {result.get("new", 0)}')
            self.stdout.write(f'   🔄 Обновлено:     {result.get("updated", 0)}')

        elif result.get('status') == 'no_users':
            self.stdout.write(
                self.style.WARNING(f'⚠️  [{source_name}] {result.get("message", "Нет пользователей")}')
            )

        else:
            error = result.get('error', 'Неизвестная ошибка')
            self.stdout.write(self.style.ERROR(f'❌ [{source_name}] Ошибка парсинга'))
            self.stdout.write(self.style.ERROR('─' * 50))
            self.stdout.write(self.style.ERROR(f'   {error}'))