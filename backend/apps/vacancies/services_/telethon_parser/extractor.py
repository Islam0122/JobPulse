import re
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VacancyExtractor:
    SALARY_PATTERNS = [
        r'(?:от\s+)?(\d+[\s\d]*)\s*(?:-|до)\s*(\d+[\s\d]*)\s*(руб|rub|₽|USD|EUR|KZT|KGS)',
        r'(?:зарплат[аы]|salary|з\.?п\.?)[:\s]+(\d+[\s\d]*)\s*(руб|rub|₽|USD|EUR|KZT|KGS)',
        r'(\d+)k?\s*[-–]\s*(\d+)k?\s*(USD|EUR|RUB)',
        r'\$(\d+)\s*[-–]\s*\$(\d+)',
    ]

    EXPERIENCE_PATTERNS = [
        r'(?:опыт|experience)[:\s]+(\d+)\+?\s*(?:лет|года?|years?)',
        r'(\d+)\+?\s*(?:лет|года?|years?)\s+(?:опыт|experience)',
        r'(junior|middle|senior|lead)',
    ]

    LOCATION_PATTERNS = [
        r'(?:город|city|location|локация)[:\s]+([A-Za-zА-Яа-я\s,]+)',
        r'📍\s*([A-Za-zА-Яа-я\s,]+)',
        r'🌍\s*([A-Za-zА-Яа-я\s,]+)',
    ]

    STACK_KEYWORDS = [
        'Python', 'Django', 'FastAPI', 'Flask', 'JavaScript', 'TypeScript',
        'React', 'Vue', 'Angular', 'Node.js', 'PostgreSQL', 'MongoDB',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Redis', 'Celery',
        'Git', 'Linux', 'CI/CD', 'Jenkins', 'GitLab', 'Java', 'Kotlin',
        'Swift', 'Go', 'Rust', 'C++', 'C#', '.NET', 'PHP', 'Laravel',
    ]

    def extract_vacancy(
            self,
            message_text: str,
            message_id: int,
            chat_username: str,
            published_date: datetime
    ) -> Optional[Dict]:
        if not self._is_vacancy(message_text):
            return None

        try:
            title = self._extract_title(message_text)
            company = self._extract_company(message_text)
            salary_from, salary_to, currency = self._extract_salary(message_text)
            location = self._extract_location(message_text)
            experience = self._extract_experience(message_text)
            skills = self._extract_skills(message_text)

            vacancy_id = f"tg_{chat_username}_{message_id}"

            return {
                'hh_id': vacancy_id,
                'title': title + ' <-- Telegram channels',
                'company_name': company or 'Не указано',
                'company_url': None,
                'description': self._clean_text(message_text),
                'salary_from': salary_from,
                'salary_to': salary_to,
                'currency': currency or 'RUB',
                'location': location or 'Удаленно',
                'experience': experience or " ",
                'employment': {'name': 'Полная занятость'},
                'schedule': {'name': ''},
                'url': f'https://t.me/{chat_username}/{message_id}',
                'skills': skills,
                'published_at': published_date.isoformat(),
                'is_active': True,
            }


        except Exception as e:
            logger.error(f"Ошибка извлечения вакансии: {e}")
            return None

    def _is_vacancy(self, text: str) -> bool:
        if not text or len(text) < 50:
            return False

        text_lower = text.lower()

        vacancy_keywords = [
            'вакансия', 'vacancy', 'требуется', 'ищем', 'нужен',
            'открыта вакансия', 'приглашаем', 'job opening',
            'hiring', 'looking for', 'we are looking',
        ]

        anti_keywords = [
            'резюме', 'ищу работу', 'cv', 'looking for job',
            'кандидат', 'соискатель', 'рекламa'
        ]

        has_vacancy_keywords = any(kw in text_lower for kw in vacancy_keywords)
        has_anti_keywords = any(kw in text_lower for kw in anti_keywords)

        return has_vacancy_keywords and not has_anti_keywords

    def _extract_title(self, text: str) -> str:
        lines = text.split('\n')
        first_line = lines[0].strip()
        title = re.sub(r'[📌💼🔥✅❗️⚡️🚀]+', '', first_line).strip()
        title = re.sub(r'^(?:вакансия|vacancy)[:\s]*', '', title, flags=re.I)
        if len(title) > 255:
            title = title[:252] + '...'

        return title or 'IT специалист'

    def _extract_company(self, text: str) -> Optional[str]:
        patterns = [
            r'(?:компания|company)[:\s]+([A-Za-zА-Яа-я0-9\s]+)',
            r'🏢\s*([A-Za-zА-Яа-я0-9\s]+)',
            r'в компанию\s+([A-Za-zА-Яа-я0-9\s]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()[:255]

        return None

    def _extract_salary(self, text: str) -> tuple:
        for pattern in self.SALARY_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) >= 3:
                        salary_from = int(groups[0].replace(' ', ''))
                        salary_to = int(groups[1].replace(' ', '')) if groups[1] else None
                        currency = self._normalize_currency(groups[2])
                    elif len(groups) == 2 and groups[1] in ['USD', 'EUR']:
                        # Формат "$3000 - $5000"
                        salary_from = int(groups[0]) * 1000
                        salary_to = int(groups[1]) * 1000
                        currency = 'USD'
                    else:
                        continue

                    return salary_from, salary_to, currency

                except (ValueError, IndexError):
                    continue

        return None, None, None

    def _normalize_currency(self, currency: str) -> str:
        currency_map = {
            'руб': 'RUB',
            'rub': 'RUB',
            '₽': 'RUB',
            'usd': 'USD',
            '$': 'USD',
            'eur': 'EUR',
            '€': 'EUR',
            'kzt': 'KZT',
            '₸': 'KZT',
            'kgs': 'KGS',
        }

        return currency_map.get(currency.lower(), 'RUB')

    def _extract_location(self, text: str) -> Optional[str]:
        remote_keywords = ['remote', 'удален', 'remotely', 'из дома']
        if any(kw in text.lower() for kw in remote_keywords):
            return 'Удаленно'

        for pattern in self.LOCATION_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                location = match.group(1).strip()
                return location[:255]

        return None

    def _extract_experience(self, text: str) -> Optional[str]:
        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                exp = match.group(1).strip()

                # Нормализация уровня
                level_map = {
                    'junior': 'Junior (0-2 года)',
                    'middle': 'Middle (2-5 лет)',
                    'senior': 'Senior (5+ лет)',
                    'lead': 'Lead (7+ лет)',
                }

                return level_map.get(exp.lower(), f'{exp} лет')

        return None

    def _extract_skills(self, text: str) -> list:
        found_skills = []
        text_upper = text.upper()

        for skill in self.STACK_KEYWORDS:
            if skill.upper() in text_upper:
                found_skills.append(skill)

        return found_skills[:10]  # Максимум 10 навыков

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 1000:
            text = text[:997] + '...'

        return text.strip()