import PyPDF2
import logging
import re

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(file_path: str) -> str:
    """
    Извлечь текст из PDF-файла

    Args:
        file_path: Путь к PDF-файлу

    Returns:
        str: Извлечённый и очищенный текст

    Raises:
        Exception: При ошибках чтения файла
    """
    try:
        text = ""

        with open(file_path, 'rb') as file:
            # Создаём PDF reader
            pdf_reader = PyPDF2.PdfReader(file)

            # Проверяем, есть ли страницы
            num_pages = len(pdf_reader.pages)

            if num_pages == 0:
                logger.warning(f"PDF файл пустой: {file_path}")
                return ""

            logger.info(f"Обработка PDF: {num_pages} страниц")

            # Извлекаем текст со всех страниц
            for page_num in range(num_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

                except Exception as e:
                    logger.error(f"Ошибка обработки страницы {page_num}: {e}")
                    continue

        # Очищаем и нормализуем текст
        cleaned_text = clean_extracted_text(text)

        logger.info(f"Извлечено символов: {len(cleaned_text)}")

        return cleaned_text

    except Exception as e:
        logger.error(f"Ошибка извлечения текста из PDF: {e}", exc_info=True)
        raise


def clean_extracted_text(text: str) -> str:
    """
    Очистить и нормализовать извлечённый текст

    Args:
        text: Сырой текст из PDF

    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""

    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)

    # Убираем повторяющиеся символы
    text = re.sub(r'(.)\1{4,}', r'\1\1\1', text)

    # Убираем спецсимволы, которые могли появиться при извлечении
    text = text.replace('\x00', '')
    text = text.replace('\ufeff', '')

    # Нормализуем пробелы вокруг знаков препинания
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])([A-Za-zА-Яа-я])', r'\1 \2', text)

    # Убираем пробелы в начале и конце
    text = text.strip()

    # Ограничиваем длину (макс 15000 символов для API)
    if len(text) > 15000:
        text = text[:15000] + "..."
        logger.warning("Текст обрезан до 15000 символов")

    return text


def validate_resume_text(text: str) -> tuple[bool, str]:
    """
    Валидация извлечённого текста резюме

    Args:
        text: Текст для проверки

    Returns:
        tuple: (is_valid, error_message)
    """
    # Минимальная длина
    if len(text.strip()) < 50:
        return False, "Текст слишком короткий (минимум 50 символов)"

    # Проверка наличия осмысленных слов
    words = re.findall(r'\b\w+\b', text)

    if len(words) < 20:
        return False, "Недостаточно слов для анализа"

    # Проверка на наличие типичных ключевых слов резюме
    resume_keywords = [
        'опыт', 'работ', 'experience', 'skills', 'education',
        'навык', 'проект', 'компани', 'должность', 'position'
    ]

    text_lower = text.lower()
    found_keywords = sum(1 for kw in resume_keywords if kw in text_lower)

    if found_keywords < 2:
        return False, "Текст не похож на резюме"

    return True, ""