from django.db import models
from apps.users.models import User, Stack, WorkFormat, EmploymentType


class Vacancy(models.Model):
    hh_id = models.CharField(
        max_length=250,
        unique=True,
        db_index=True,
        verbose_name="ID"
    )

    title = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Название вакансии"
    )

    company_name = models.CharField(
        max_length=255,
        verbose_name="Компания"
    )

    company_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на компанию"
    )

    description = models.TextField(
        verbose_name="Описание"
    )

    salary_from = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Зарплата от"
    )

    salary_to = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Зарплата до"
    )

    currency = models.CharField(
        max_length=5,
        default="RUR",
        verbose_name="Валюта"
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Город"
    )

    experience = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Требуемый опыт"
    )

    employment = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Тип занятости"
    )

    schedule = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="График работы"
    )

    url = models.URLField(
        verbose_name="Ссылка на вакансию"
    )

    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Требуемые навыки"
    )

    published_at = models.DateTimeField(
        verbose_name="Дата публикации"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Активна"
    )

    notified_users = models.ManyToManyField(
        User,
        through='VacancyNotification',
        related_name='notified_vacancies',
        verbose_name="Уведомленные пользователи"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено в БД"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["is_active", "-published_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.company_name}"

    @property
    def salary_range(self):
        if self.salary_from and self.salary_to:
            return f"{self.salary_from} - {self.salary_to} {self.currency}"
        elif self.salary_from:
            return f"от {self.salary_from} {self.currency}"
        elif self.salary_to:
            return f"до {self.salary_to} {self.currency}"
        return "Не указана"


class VacancyNotification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        verbose_name="Вакансия"
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Отправлено"
    )

    is_viewed = models.BooleanField(
        default=False,
        verbose_name="Просмотрено"
    )
    viewed_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        verbose_name = "Уведомление о вакансии"
        verbose_name_plural = "Уведомления о вакансиях"
        unique_together = [["user", "vacancy"]]
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.user.telegram_id} - {self.vacancy.title}"


class ParsingLog(models.Model):
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Начало парсинга"
    )

    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Завершение"
    )

    total_found = models.IntegerField(
        default=0,
        verbose_name="Найдено вакансий"
    )

    new_vacancies = models.IntegerField(
        default=0,
        verbose_name="Новых вакансий"
    )

    updated_vacancies = models.IntegerField(
        default=0,
        verbose_name="Обновлено"
    )

    errors = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ошибки"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "В процессе"),
            ("completed", "Завершено"),
            ("failed", "Ошибка"),
        ],
        default="running",
        verbose_name="Статус"
    )

    class Meta:
        verbose_name = "Лог парсинга"
        verbose_name_plural = "Логи парсинга"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Парсинг {self.started_at.strftime('%d.%m.%Y %H:%M')}"


class VacancyReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Интересно'),
        ('dislike', 'Не подходит'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vacancy_reactions',
        verbose_name="Пользователь"
    )

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name="Вакансия"
    )

    reaction = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        verbose_name="Реакция"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата реакции"
    )

    class Meta:
        verbose_name = "Реакция на вакансию"
        verbose_name_plural = "Реакции на вакансии"
        unique_together = [['user', 'vacancy']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.telegram_id} - {self.vacancy.title} ({self.reaction})"


class FavoriteVacancy(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_vacancies',
        verbose_name="Пользователь"
    )

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="Вакансия"
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено в избранное"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Заметки пользователя"
    )

    class Meta:
        verbose_name = "Избранная вакансия"
        verbose_name_plural = "Избранные вакансии"
        unique_together = [['user', 'vacancy']]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.telegram_id} - {self.vacancy.title}"

