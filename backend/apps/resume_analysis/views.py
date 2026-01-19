from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ResumeAnalysisSerializer
from .services.ai_checker import *
from .models import ResumeAnalysis
from django.db import transaction


def analyze_resume(analysis: ResumeAnalysis) -> ResumeAnalysis:
    analysis.status = "processing"
    analysis.save(update_fields=["status"])

    try:
        raw_response = analyze_resume_with_ai(analysis.resume_text)
        parsed_result = parse_ai_response(raw_response)

        with transaction.atomic():
            analysis.result = parsed_result
            analysis.status = "done"
            analysis.error = ""
            analysis.save(update_fields=["result", "status", "error"])

        return analysis

    except Exception as e:
        analysis.status = "failed"
        analysis.error = str(e)
        analysis.save(update_fields=["status", "error"])
        raise


class ResumeAnalysisCreateView(APIView):
    def post(self, request):
        serializer = ResumeAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analysis = serializer.save(status="pending")


        analysis = analyze_resume(analysis)

        return Response(
                {
                    "status": analysis.status,
                    "result": analysis.result,
                },
                status=status.HTTP_200_OK
            )


