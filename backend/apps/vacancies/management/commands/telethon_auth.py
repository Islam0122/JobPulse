import asyncio
from django.core.management.base import BaseCommand
from apps.vacancies.services_.telethon_parser.client import TelethonClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
import os


class Command(BaseCommand):
    help = 'Авторизация Telethon клиента'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            help='Код подтверждения из Telegram'
        )

        parser.add_argument(
            '--password',
            type=str,
            help='Пароль 2FA (если включен)'
        )

        parser.add_argument(
            '--send-code',
            action='store_true',
            help='Отправить новый код'
        )

        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить сессию и начать заново'
        )

    def handle(self, *args, **options):
        code = options.get('code')
        password = options.get('password')
        send_code = options.get('send_code')
        reset = options.get('reset')

        async def auth():
            client_wrapper = TelethonClient()

            # Сброс сессии
            if reset:
                session_path = os.path.join(
                    client_wrapper.session_name + '.session'
                )
                if os.path.exists(session_path):
                    os.remove(session_path)
                    self.stdout.write(self.style.SUCCESS('✅ Сессия удалена'))
                return

            client = await client_wrapper.get_client()

            try:
                # Проверка текущей авторизации
                if await client.is_user_authorized():
                    me = await client.get_me()
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Уже авторизован!')
                    )
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write('')
                    self.stdout.write(f'👤 Имя: {me.first_name} {me.last_name or ""}')
                    self.stdout.write(f'📝 Username: @{me.username}')
                    self.stdout.write(f'🆔 ID: {me.id}')
                    self.stdout.write('')
                    return

                # Отправка нового кода
                if send_code:
                    await client.send_code_request(client_wrapper.phone)
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write(self.style.SUCCESS('📱 Новый код отправлен'))
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write('')
                    self.stdout.write('Введи код командой:')
                    self.stdout.write(
                        self.style.WARNING('python manage.py telethon_auth --code=XXXXX')
                    )
                    self.stdout.write('')
                    return

                # Ввод кода (БЕЗ повторной отправки)
                if code and not password:
                    try:
                        await client.sign_in(client_wrapper.phone, code)

                        me = await client.get_me()
                        self.stdout.write('')
                        self.stdout.write(self.style.SUCCESS('═' * 60))
                        self.stdout.write(self.style.SUCCESS('✅ Авторизация успешна!'))
                        self.stdout.write(self.style.SUCCESS('═' * 60))
                        self.stdout.write('')
                        self.stdout.write(f'👤 Имя: {me.first_name}')
                        self.stdout.write(f'📝 Username: @{me.username}')
                        self.stdout.write(f'🆔 ID: {me.id}')
                        self.stdout.write('')

                    except SessionPasswordNeededError:
                        self.stdout.write('')
                        self.stdout.write(self.style.WARNING('═' * 60))
                        self.stdout.write(
                            self.style.WARNING('🔐 Требуется пароль 2FA')
                        )
                        self.stdout.write(self.style.WARNING('═' * 60))
                        self.stdout.write('')
                        self.stdout.write('Введи пароль командой:')
                        self.stdout.write(
                            self.style.WARNING(
                                f'python manage.py telethon_auth --password=YOUR_PASSWORD'
                            )
                        )
                        self.stdout.write('')
                        self.stdout.write('⚠️  НЕ вводи --code повторно!')
                        self.stdout.write('')

                    except PhoneCodeInvalidError:
                        self.stdout.write(self.style.ERROR('❌ Неверный код'))
                        self.stdout.write('')
                        self.stdout.write('Запроси новый код:')
                        self.stdout.write(
                            self.style.WARNING('python manage.py telethon_auth --send-code')
                        )
                        self.stdout.write('')

                    except PhoneCodeExpiredError:
                        self.stdout.write(self.style.ERROR('❌ Код истёк'))
                        self.stdout.write('')
                        self.stdout.write('Запроси новый код:')
                        self.stdout.write(
                            self.style.WARNING('python manage.py telethon_auth --send-code')
                        )
                        self.stdout.write('')

                # Ввод пароля 2FA (БЕЗ кода)
                elif password and not code:
                    try:
                        await client.sign_in(password=password)

                        me = await client.get_me()
                        self.stdout.write('')
                        self.stdout.write(self.style.SUCCESS('═' * 60))
                        self.stdout.write(self.style.SUCCESS('✅ Авторизация с 2FA успешна!'))
                        self.stdout.write(self.style.SUCCESS('═' * 60))
                        self.stdout.write('')
                        self.stdout.write(f'👤 Имя: {me.first_name}')
                        self.stdout.write(f'📝 Username: @{me.username}')
                        self.stdout.write(f'🆔 ID: {me.id}')
                        self.stdout.write('')

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'❌ Неверный пароль: {e}'))
                        self.stdout.write('')

                # Ввод кода И пароля одновременно (НЕПРАВИЛЬНО)
                elif code and password:
                    self.stdout.write('')
                    self.stdout.write(self.style.ERROR('═' * 60))
                    self.stdout.write(self.style.ERROR('❌ НЕПРАВИЛЬНОЕ ИСПОЛЬЗОВАНИЕ'))
                    self.stdout.write(self.style.ERROR('═' * 60))
                    self.stdout.write('')
                    self.stdout.write('Правильная последовательность:')
                    self.stdout.write('')
                    self.stdout.write('1️⃣  Отправить код:')
                    self.stdout.write('    python manage.py telethon_auth --send-code')
                    self.stdout.write('')
                    self.stdout.write('2️⃣  Ввести код из Telegram:')
                    self.stdout.write('    python manage.py telethon_auth --code=XXXXX')
                    self.stdout.write('')
                    self.stdout.write('3️⃣  Если требуется 2FA, ввести пароль:')
                    self.stdout.write('    python manage.py telethon_auth --password=YOUR_PASSWORD')
                    self.stdout.write('')

                # Без параметров - отправляем код
                else:
                    await client.send_code_request(client_wrapper.phone)
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write(self.style.SUCCESS('📱 Код отправлен'))
                    self.stdout.write(self.style.SUCCESS('═' * 60))
                    self.stdout.write('')
                    self.stdout.write('Введи код командой:')
                    self.stdout.write(
                        self.style.WARNING('python manage.py telethon_auth --code=XXXXX')
                    )
                    self.stdout.write('')

            except Exception as e:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR('═' * 60))
                self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))
                self.stdout.write(self.style.ERROR('═' * 60))
                self.stdout.write('')

                error_str = str(e).lower()

                if 'sendcodeunavailable' in error_str or 'flood' in error_str:
                    self.stdout.write('💡 Telegram заблокировал отправку кодов.')
                    self.stdout.write('   Подожди 24 часа и попробуй снова.')
                    self.stdout.write('')
                    self.stdout.write('   Или используй другой номер телефона.')
                    self.stdout.write('')

        asyncio.run(auth())