from django.core.management.base import BaseCommand
from apps.users.models import User, Stack, WorkFormat, EmploymentType


class Command(BaseCommand):
    help = 'Создание тестовых пользователей и справочников'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Создание справочников и тестовых данных...'))
        self.stdout.write('')

        self.stdout.write(self.style.WARNING('📚 Создание технологий...'))
        stacks = [
            'Python', 'JavaScript', 'TypeScript', 'React', 'Django',
            'FastAPI', 'PostgreSQL', 'Docker', 'AWS', 'Git',
            'Redis', 'Celery', 'Node.js', 'Vue.js', 'MongoDB'
        ]

        stack_objects = []
        for stack_name in stacks:
            stack, created = Stack.objects.get_or_create(name=stack_name)
            stack_objects.append(stack)
            if created:
                self.stdout.write(f'  ✓ Создан стек: {stack_name}')

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('💼 Создание форматов работы...'))
        work_formats_data = [
            ('remote', 'Remote / Удалённо'),
            ('office', 'Office / Офис'),
            ('hybrid', 'Hybrid / Гибрид'),
        ]

        work_format_objects = []
        for code, title in work_formats_data:
            wf, created = WorkFormat.objects.get_or_create(
                code=code,
                defaults={'title': title}
            )
            work_format_objects.append(wf)
            if created:
                self.stdout.write(f'  ✓ Создан формат: {title}')

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📋 Создание типов занятости...'))
        employment_types_data = [
            ('full_time', 'Full-time / Полная занятость'),
            ('part_time', 'Part-time / Частичная занятость'),
            ('contract', 'Contract / Контракт'),
            ('freelance', 'Freelance / Фриланс'),
        ]

        employment_type_objects = []
        for code, title in employment_types_data:
            et, created = EmploymentType.objects.get_or_create(
                code=code,
                defaults={'title': title}
            )
            employment_type_objects.append(et)
            if created:
                self.stdout.write(f'  ✓ Создан тип: {title}')

        # Создание тестовых пользователей
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('👥 Создание тестовых пользователей...'))

        test_users = [
            {
                'telegram_id': 123456789,
                'username': 'john_doe',
                'role': 'Backend Developer',
                'level': 'middle',
                'location': 'Moscow',
                'salary_from': 3000,
                'currency': 'USD',
                'is_profile_completed': True,
                'stacks': ['Python', 'Django', 'PostgreSQL', 'Redis', 'Docker'],
                'work_formats': ['remote'],
                'employment_types': ['full_time'],
            },
            {
                'telegram_id': 987654321,
                'username': 'jane_smith',
                'role': 'Frontend Developer',
                'level': 'senior',
                'location': 'Saint Petersburg',
                'salary_from': 4000,
                'currency': 'USD',
                'is_profile_completed': True,
                'stacks': ['JavaScript', 'TypeScript', 'React', 'Vue.js'],
                'work_formats': ['remote', 'hybrid'],
                'employment_types': ['full_time', 'contract'],
            },
            {
                'telegram_id': 555555555,
                'username': 'alex_tech',
                'role': 'Full Stack Developer',
                'level': 'junior',
                'location': 'Remote',
                'salary_from': 2000,
                'currency': 'USD',
                'is_profile_completed': False,
                'onboarding_step': 'stack_selection',
                'stacks': ['Python', 'JavaScript', 'Node.js'],
                'work_formats': ['remote'],
                'employment_types': ['full_time', 'part_time'],
            },
            {
                'telegram_id': 111222333,
                'username': 'maria_dev',
                'role': 'DevOps Engineer',
                'level': 'middle',
                'location': 'Novosibirsk',
                'salary_from': 3500,
                'currency': 'USD',
                'is_profile_completed': True,
                'stacks': ['Docker', 'AWS', 'Git', 'PostgreSQL'],
                'work_formats': ['office', 'hybrid'],
                'employment_types': ['full_time'],
            },
            {
                'telegram_id': 444555666,
                'username': 'peter_code',
                'role': 'Data Scientist',
                'level': 'senior',
                'location': 'Kazan',
                'salary_from': 4500,
                'currency': 'USD',
                'is_profile_completed': True,
                'stacks': ['Python', 'MongoDB', 'PostgreSQL'],
                'work_formats': ['remote'],
                'employment_types': ['contract', 'freelance'],
            },
        ]

        for user_data in test_users:
            # Извлекаем связанные данные
            stacks = user_data.pop('stacks', [])
            work_formats = user_data.pop('work_formats', [])
            employment_types = user_data.pop('employment_types', [])

            user, created = User.objects.get_or_create(
                telegram_id=user_data['telegram_id'],
                defaults=user_data
            )

            if created:
                stack_objs = Stack.objects.filter(name__in=stacks)
                user.stack.add(*stack_objs)

                wf_objs = WorkFormat.objects.filter(code__in=work_formats)
                user.work_formats.add(*wf_objs)

                et_objs = EmploymentType.objects.filter(code__in=employment_types)
                user.employment_types.add(*et_objs)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Создан: {user.username} (ID: {user.telegram_id}) - {user.role}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Существует: {user.username} (ID: {user.telegram_id})'
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('════════════════════════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS('✅ Все тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('════════════════════════════════════════════════════════'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📊 Статистика:'))
        self.stdout.write(f'   Технологий: {Stack.objects.count()}')
        self.stdout.write(f'   Форматов работы: {WorkFormat.objects.count()}')
        self.stdout.write(f'   Типов занятости: {EmploymentType.objects.count()}')
        self.stdout.write(f'   Пользователей: {User.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🌐 API доступно:'))
        self.stdout.write('   http://localhost:8000/api/users/')
        self.stdout.write('   http://localhost:8000/api/swagger/')
        self.stdout.write('')