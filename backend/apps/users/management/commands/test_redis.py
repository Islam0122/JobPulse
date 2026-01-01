from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.users.tasks import send_notification
import redis as redis_client


class Command(BaseCommand):
    help = 'Тест Redis подключения и Celery'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🔴 Тестирование Redis...'))
        self.stdout.write('')

        try:
            from django.conf import settings
            redis_url = settings.REDIS_URL
            r = redis_client.from_url(redis_url)
            r.ping()
            self.stdout.write(self.style.SUCCESS('✓ Прямое подключение к Redis работает'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка прямого подключения: {e}'))

        try:
            test_key = 'test_key'
            test_value = 'test_value_123'

            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)

            if retrieved_value == test_value:
                self.stdout.write(self.style.SUCCESS('✓ Django Cache работает'))
                cache.delete(test_key)
            else:
                self.stdout.write(self.style.ERROR(f'✗ Cache вернул неверное значение: {retrieved_value}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка Cache: {e}'))

        try:
            test_data = {
                'user_id': 123,
                'name': 'Test User',
                'items': [1, 2, 3],
                'nested': {'key': 'value'}
            }

            cache.set('complex_test', test_data, 60)
            retrieved_data = cache.get('complex_test')

            if retrieved_data == test_data:
                self.stdout.write(self.style.SUCCESS('✓ Сложные объекты в кэше работают'))
                cache.delete('complex_test')
            else:
                self.stdout.write(self.style.ERROR('✗ Ошибка при работе со сложными объектами'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка сложных объектов: {e}'))

        try:
            cache.set('pattern_test_1', 'value1', 60)
            cache.set('pattern_test_2', 'value2', 60)

            val1 = cache.get('pattern_test_1')
            val2 = cache.get('pattern_test_2')

            if val1 and val2:
                self.stdout.write(self.style.SUCCESS('✓ Множественные ключи работают'))


            cache.delete('pattern_test_1')
            cache.delete('pattern_test_2')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка pattern: {e}'))

        try:
            result = send_notification.delay(123456789, 'Test message')
            self.stdout.write(self.style.SUCCESS(f'✓ Celery task создана (ID: {result.id})'))
            self.stdout.write(self.style.WARNING('  ⚠️  Убедитесь что Celery worker запущен для обработки'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Celery недоступен: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('════════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS('✅ Тестирование Redis завершено!'))
        self.stdout.write(self.style.SUCCESS('════════════════════════════════════════'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📊 Для мониторинга Redis выполните:'))
        self.stdout.write('   redis-cli MONITOR')
        self.stdout.write('')