import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .serializers import ResumeAnalysisSerializer
from .services.ai_checker import analyze_resume_with_ai, GigaChatAPIError
from .models import ResumeAnalysis

logger = logging.getLogger(__name__)


class ResumeAnalysisCreateView(APIView):
    """
    API endpoint для создания и анализа резюме

    POST /api/resume-analysis/
    Body:
    {
        "telegram_id": 123456789,
        "resume_text": "Мой опыт работы..."
    }

    Response (Success):
    {
        "status": "done",
        "result": {
            "summary": "...",
            "detected_domain": "IT",
            "strengths": [...],
            "weaknesses": [...],
            "recommendations": [...],
            "overall_score": 7.5
        }
    }

    Response (Error):
    {
        "status": "failed",
        "error": "Описание ошибки"
    }
    """

    def post(self, request):
        """Создание и синхронный анализ резюме"""

        # 1. Валидация входных данных
        serializer = ResumeAnalysisSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Невалидные данные: {serializer.errors}")
            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Создание записи в БД со статусом "pending"
        try:
            with transaction.atomic():
                analysis = serializer.save(status="pending")
                logger.info(f"Создана запись анализа #{analysis.id} для пользователя {analysis.user.telegram_id}")
        except Exception as e:
            logger.error(f"Ошибка создания записи: {e}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "error": "Ошибка создания записи в БД"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. Синхронный анализ
        try:
            analysis = self._analyze_resume_sync(analysis)

            return Response(
                {
                    "id": analysis.id,
                    "status": analysis.status,
                    "result": analysis.result,
                    "created_at": analysis.created_at
                },
                status=status.HTTP_200_OK
            )

        except GigaChatAPIError as e:
            # Ошибка API - возвращаем понятное сообщение
            logger.error(f"GigaChat API error для анализа #{analysis.id}: {e}")

            with transaction.atomic():
                analysis.status = "failed"
                analysis.error = f"Ошибка AI сервиса: {str(e)}"
                analysis.save(update_fields=["status", "error"])

            return Response(
                {
                    "id": analysis.id,
                    "status": "failed",
                    "error": "Временная ошибка AI сервиса. Попробуйте позже.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except ValueError as e:
            # Ошибка валидации данных
            logger.error(f"Validation error для анализа #{analysis.id}: {e}")

            with transaction.atomic():
                analysis.status = "failed"
                analysis.error = str(e)
                analysis.save(update_fields=["status", "error"])

            return Response(
                {
                    "id": analysis.id,
                    "status": "failed",
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Неожиданная ошибка
            logger.error(f"Unexpected error для анализа #{analysis.id}: {e}", exc_info=True)

            with transaction.atomic():
                analysis.status = "failed"
                analysis.error = "Внутренняя ошибка сервера"
                analysis.save(update_fields=["status", "error"])

            return Response(
                {
                    "id": analysis.id,
                    "status": "failed",
                    "error": "Внутренняя ошибка сервера"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _analyze_resume_sync(self, analysis: ResumeAnalysis) -> ResumeAnalysis:
        """
        Синхронный анализ резюме

        Args:
            analysis: Объект ResumeAnalysis

        Returns:
            ResumeAnalysis: Обновлённый объект

        Raises:
            GigaChatAPIError: Ошибка API
            ValueError: Ошибка валидации
            Exception: Другие ошибки
        """
        logger.info(f"Начало анализа #{analysis.id}")

        # Обновляем статус на "processing"
        with transaction.atomic():
            analysis.status = "processing"
            analysis.save(update_fields=["status"])

        # Вызов AI анализа
        raw_response = analyze_resume_with_ai(analysis.resume_text)

        logger.info(f"AI анализ #{analysis.id} завершён успешно")

        # Сохранение результата
        with transaction.atomic():
            analysis.result = raw_response
            analysis.status = "done"
            analysis.error = ""
            analysis.save(update_fields=["result", "status", "error"])

        logger.info(f"Результат анализа #{analysis.id} сохранён")

        return analysis


class ResumeAnalysisDetailView(APIView):
    """
    Получение результата анализа по ID

    GET /api/resume-analysis/{id}/
    """

    def get(self, request, pk):
        """Получение анализа по ID"""
        try:
            analysis = ResumeAnalysis.objects.select_related('user').get(pk=pk)

            return Response({
                "id": analysis.id,
                "status": analysis.status,
                "result": analysis.result,
                "error": analysis.error,
                "created_at": analysis.created_at,
                "user_id": analysis.user.telegram_id
            })

        except ResumeAnalysis.DoesNotExist:
            return Response(
                {"error": "Анализ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class ResumeAnalysisListView(APIView):
    """
    Список анализов пользователя

    GET /api/resume-analysis/?telegram_id=123456789
    """

    def get(self, request):
        """Получение списка анализов пользователя"""
        telegram_id = request.query_params.get('telegram_id')

        if not telegram_id:
            return Response(
                {"error": "Требуется параметр telegram_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        analyses = ResumeAnalysis.objects.filter(
            user__telegram_id=telegram_id
        ).order_by('-created_at')[:10]

        data = [{
            "id": a.id,
            "status": a.status,
            "created_at": a.created_at,
            "has_result": bool(a.result)
        } for a in analyses]

        return Response({
            "count": len(data),
            "results": data
        })