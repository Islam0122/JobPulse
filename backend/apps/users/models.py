from django.db import models
from django.utils import timezone

class Level(models.TextChoices):
    JUNIOR = "junior", "Junior / Джуниор"
    MIDDLE = "middle", "Middle / Мидл"
    SENIOR = "senior", "Senior / Сеньор"
    LEAD = "lead", "Lead / Лид"


class NotifyMode(models.TextChoices):
    INSTANT = "instant", "Instant / Сразу"
    DAILY = "daily", "Daily / Ежедневно"
    WEEKLY = "weekly", "Weekly / Еженедельно"


class WorkFormat(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True
    )  # remote / office / hybrid

    title = models.CharField(
        max_length=50,
        verbose_name="Title / Название"
    )

    class Meta:
        verbose_name = "Work format / Формат работы"
        verbose_name_plural = "Work formats / Форматы работы"

    def __str__(self):
        return self.title


class Stack(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Technology / Технология"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Stack / Стек"
        verbose_name_plural = "Stacks / Стеки"

    def __str__(self):
        return self.name


class EmploymentType(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True
    )  # full_time / part_time / contract / freelance

    title = models.CharField(
        max_length=50,
        verbose_name="Title / Название"
    )

    class Meta:
        verbose_name = "Employment type / Тип занятости"
        verbose_name_plural = "Employment types / Типы занятости"

    def __str__(self):
        return self.title


class User(models.Model):
    telegram_id = models.BigIntegerField(
        unique=True,
        db_index=True,
        verbose_name="Telegram ID"
    )

    username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Username / Ник"
    )

    role = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Role / Роль"
    )

    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        blank=True,
        null=True,
        verbose_name="Level / Уровень"
    )

    stack = models.ManyToManyField(
        Stack,
        blank=True,
        related_name="users",
        verbose_name="Tech stack / Стек технологий"
    )

    work_formats = models.ManyToManyField(
        WorkFormat,
        blank=True,
        related_name="users",
        verbose_name="Work formats / Форматы работы"
    )

    employment_types = models.ManyToManyField(
        EmploymentType,
        blank=True,
        related_name="users",
        verbose_name="Employment types / Типы занятости"
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Location / Локация"
    )

    salary_from = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Salary from / Зарплата от"
    )

    currency = models.CharField(
        max_length=5,
        default="USD",
        verbose_name="Currency / Валюта"
    )

    notify_mode = models.CharField(
        max_length=10,
        choices=NotifyMode.choices,
        default=NotifyMode.DAILY,
        verbose_name="Notification mode / Уведомления"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active / Активен"
    )

    is_profile_completed = models.BooleanField(
        default=False,
        verbose_name="Profile completed / Профиль заполнен"
    )

    onboarding_step = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Onboarding step / Шаг онбординга"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Created at / Создан"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at / Обновлён"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User / Пользователь"
        verbose_name_plural = "Users / Пользователи"

    def __str__(self):
        return f"{self.telegram_id} | {self.role}"


