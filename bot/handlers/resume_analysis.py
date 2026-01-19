from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
from services.pdf_extractor import extract_text_from_pdf
import logging
import html
import asyncio

logger = logging.getLogger(__name__)
router = Router()

logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"


class ResumeAnalysisStates(StatesGroup):
    """Состояния для процесса анализа резюме"""
    waiting_for_pdf = State()
    processing = State()


@router.message(Command("analyze"))
async def cmd_analyze(message: Message, state: FSMContext):
    """
    Команда /analyze - начало процесса анализа резюме
    """
    telegram_id = message.from_user.id

    # Проверяем, есть ли у пользователя профиль
    user = await api.get_user(telegram_id)

    if not user:
        await message.answer(
            "⚠️ <b>Сначала создай профиль</b>\n\n"
            "Используй команду /start для регистрации",
            parse_mode="HTML"
        )
        return

    # Устанавливаем состояние ожидания PDF
    await state.set_state(ResumeAnalysisStates.waiting_for_pdf)

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="analyze:cancel")

    msg = await message.answer_photo(
        photo=logo,
        caption=(
            "📄 <b>Анализ резюме</b>\n\n"
            "Отправь мне своё резюме в формате <b>PDF</b>,\n"
            "и я проанализирую его с помощью AI.\n\n"
            "✨ <b>Что я оценю:</b>\n"
            "• Сильные стороны\n"
            "• Области для улучшения\n"
            "• Рекомендации по доработке\n"
            "• Актуальные навыки для рынка\n"
            "• Конкурентоспособность\n\n"
            "📎 Жду PDF-файл..."
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await state.update_data(message_id=msg.message_id)


@router.callback_query(F.data == "analyze:cancel")
async def cancel_analysis(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса анализа"""
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Попробовать снова", callback_data="analyze:restart")
    builder.button(text="🏠 Главное меню", callback_data="menu:home")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption="❌ <b>Анализ отменён</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "analyze:restart")
async def restart_analysis(callback: CallbackQuery, state: FSMContext):
    """Перезапуск анализа"""
    await state.set_state(ResumeAnalysisStates.waiting_for_pdf)

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="analyze:cancel")

    await callback.message.edit_caption(
        caption=(
            "📄 <b>Анализ резюме</b>\n\n"
            "Отправь мне своё резюме в формате <b>PDF</b>,\n"
            "и я проанализирую его с помощью AI.\n\n"
            "✨ <b>Что я оценю:</b>\n"
            "• Сильные стороны\n"
            "• Области для улучшения\n"
            "• Рекомендации по доработке\n"
            "• Актуальные навыки для рынка\n"
            "• Конкурентоспособность\n\n"
            "📎 Жду PDF-файл..."
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.message(ResumeAnalysisStates.waiting_for_pdf, F.document)
async def process_resume_pdf(message: Message, state: FSMContext, bot: Bot):
    """
    Обработка PDF-файла с резюме
    """
    document = message.document

    # Проверяем формат файла
    if not document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "⚠️ <b>Неверный формат</b>\n\n"
            "Пожалуйста, отправь файл в формате <b>PDF</b>",
            parse_mode="HTML"
        )
        return

    # Проверяем размер файла (макс 10 МБ)
    if document.file_size > 10 * 1024 * 1024:
        await message.answer(
            "⚠️ <b>Файл слишком большой</b>\n\n"
            "Максимальный размер: 10 МБ",
            parse_mode="HTML"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    old_message_id = data.get('message_id')

    # Удаляем старое сообщение
    if old_message_id:
        try:
            await bot.delete_message(message.chat.id, old_message_id)
        except:
            pass

    # Удаляем сообщение пользователя с файлом
    try:
        await message.delete()
    except:
        pass

    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer_photo(
        photo=logo,
        caption=(
            "⏳ <b>Обрабатываю резюме...</b>\n\n"
            "📄 Извлекаю текст из PDF\n"
            "🤖 Подготавливаю для AI-анализа\n\n"
            "Это может занять до минуты ⏱"
        ),
        parse_mode="HTML"
    )

    await state.set_state(ResumeAnalysisStates.processing)

    try:
        # Скачиваем файл
        file = await bot.get_file(document.file_id)
        file_path = file.file_path

        # Создаём временный путь для сохранения
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, f"resume_{message.from_user.id}.pdf")

        # Скачиваем файл
        await bot.download_file(file_path, local_path)

        # Извлекаем текст из PDF
        resume_text = await extract_text_from_pdf(local_path)

        # Удаляем временный файл
        try:
            os.remove(local_path)
        except:
            pass

        if not resume_text or len(resume_text.strip()) < 50:
            await processing_msg.edit_caption(
                caption=(
                    "❌ <b>Не удалось извлечь текст</b>\n\n"
                    "Возможные причины:\n"
                    "• PDF состоит только из изображений\n"
                    "• Файл защищён паролем\n"
                    "• Файл повреждён\n\n"
                    "💡 Попробуй:\n"
                    "• Пересохранить PDF с текстовым слоем\n"
                    "• Использовать другой файл"
                ),
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Обновляем сообщение
        await processing_msg.answer(
            text=(
                "✅ <b>Текст извлечён</b>\n\n"
                "📊 Объём текста: ~{} символов\n\n"
                "🤖 Отправляю на AI-анализ...\n"
                "Это займёт 30-60 секунд ⏱"
            ).format(len(resume_text)),
            parse_mode="HTML"
        )

        # Отправляем на анализ через API
        telegram_id = message.from_user.id

        result = await api.analyze_resume(
            telegram_id=telegram_id,
            resume_text=resume_text
        )

        if not result:
            await processing_msg.edit_caption(
                caption=(
                    "❌ <b>Ошибка анализа</b>\n\n"
                    "Не удалось отправить резюме на анализ.\n"
                    "Попробуй позже 🙏"
                ),
                parse_mode="HTML"
            )
            await state.clear()
            return

        analysis_id = result.get('id')

        # Ждём результата анализа (polling)
        await processing_msg.edit_caption(
            caption=(
                "🔄 <b>AI анализирует резюме...</b>\n\n"
                "⏳ Пожалуйста, подожди\n"
                "Анализ может занять до минуты"
            ),
            parse_mode="HTML"
        )

        # Polling результата (максимум 60 секунд)
        for attempt in range(30):  # 30 попыток по 2 секунды = 60 сек
            await asyncio.sleep(2)

            analysis = await api.get_resume_analysis(analysis_id)

            if not analysis:
                continue

            status = analysis.get('status')

            if status == 'done':
                # Анализ завершён успешно
                await show_analysis_result(
                    processing_msg,
                    analysis,
                    state
                )
                return

            elif status == 'failed':
                # Ошибка анализа
                error = analysis.get('error', 'Неизвестная ошибка')
                await processing_msg.edit_caption(
                    caption=(
                        "❌ <b>Ошибка AI-анализа</b>\n\n"
                        f"Причина: {html.escape(error)}\n\n"
                        "Попробуй позже 🙏"
                    ),
                    parse_mode="HTML"
                )
                await state.clear()
                return

        # Таймаут ожидания
        await processing_msg.edit_caption(
            caption=(
                "⏱ <b>Превышено время ожидания</b>\n\n"
                "Анализ занимает больше времени, чем обычно.\n"
                "Результат придёт позже в уведомлении 📬"
            ),
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка обработки резюме: {e}", exc_info=True)

        await processing_msg.edit_caption(
            caption=(
                "❌ <b>Произошла ошибка</b>\n\n"
                "Не удалось обработать файл.\n"
                "Попробуй позже 🙏"
            ),
            parse_mode="HTML"
        )
        await state.clear()


async def show_analysis_result(message: Message, analysis: dict, state: FSMContext):
    """
    Показать результат анализа резюме
    """
    result = analysis.get('result', {})

    # Формируем текст результата
    text = "✅ <b>Анализ резюме завершён!</b>\n\n"

    # Общая информация
    summary = result.get('summary', '')
    if summary:
        text += f"📋 <b>Краткое резюме:</b>\n{html.escape(summary)}\n\n"

    # Детектированная область и уровень
    domain = result.get('detected_domain', 'unknown')
    level = result.get('detected_level', 'unknown')

    domain_emoji = {
        'IT': '💻',
        'design': '🎨',
        'marketing': '📈',
        'finance': '💰',
        'sales': '💼',
        'management': '👔',
        'other': '📊',
        'unknown': '❓'
    }

    level_emoji = {
        'junior': '🌱',
        'middle': '🌿',
        'senior': '🌳',
        'lead': '👑',
        'unknown': '❓'
    }

    text += f"{domain_emoji.get(domain, '📊')} <b>Область:</b> {domain.capitalize()}\n"
    text += f"{level_emoji.get(level, '❓')} <b>Уровень:</b> {level.capitalize()}\n\n"

    # Оценка
    score = result.get('overall_score', 0)
    score_emoji = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
    text += f"{score_emoji} <b>Общая оценка:</b> {score}/10\n\n"

    # Конкурентоспособность
    competitiveness = result.get('market_competitiveness', 'unknown')
    comp_text = {
        'high': '🔥 Высокая',
        'medium': '✅ Средняя',
        'low': '⚠️ Низкая',
        'unknown': '❓ Не определена'
    }
    text += f"📊 <b>Конкурентоспособность:</b> {comp_text.get(competitiveness, '❓')}\n\n"

    # Сильные стороны
    strengths = result.get('strengths', [])
    if strengths:
        text += "💪 <b>Сильные стороны:</b>\n"
        for i, strength in enumerate(strengths[:5], 1):
            text += f"{i}. {html.escape(strength)}\n"
        text += "\n"

    # Слабые стороны
    weaknesses = result.get('weaknesses', [])
    if weaknesses:
        text += "⚠️ <b>Что можно улучшить:</b>\n"
        for i, weakness in enumerate(weaknesses[:5], 1):
            text += f"{i}. {html.escape(weakness)}\n"
        text += "\n"

    # Рекомендации
    recommendations = result.get('recommendations', [])
    if recommendations:
        text += "💡 <b>Рекомендации:</b>\n"
        for i, rec in enumerate(recommendations[:3], 1):
            text += f"{i}. {html.escape(rec)}\n"
        text += "\n"

    # Навыки для развития
    skills = result.get('skills_to_develop', [])
    if skills:
        text += "🎯 <b>Навыки для развития:</b>\n"
        text += ", ".join([html.escape(s) for s in skills[:7]])
        if len(skills) > 7:
            text += f" и ещё {len(skills) - 7}"
        text += "\n\n"

    # Тренды рынка
    trends = result.get('market_trends_advice', [])
    if trends:
        text += "📈 <b>Актуальные тренды:</b>\n"
        for i, trend in enumerate(trends[:3], 1):
            text += f"{i}. {html.escape(trend)}\n"


    await message.answer(
        text=text,
        parse_mode="HTML",
    )

    await state.clear()


@router.message(ResumeAnalysisStates.waiting_for_pdf)
async def wrong_file_type(message: Message):
    """
    Обработка неправильного типа файла
    """
    await message.answer(
        "⚠️ <b>Пожалуйста, отправь PDF-файл</b>\n\n"
        "Я принимаю только документы в формате PDF 📄",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "analyze:start")
async def start_analysis_from_menu(callback: CallbackQuery, state: FSMContext):
    """Запуск анализа из главного меню"""
    await state.set_state(ResumeAnalysisStates.waiting_for_pdf)

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="analyze:cancel")

    await callback.message.edit_caption(
        caption=(
            "📄 <b>Анализ резюме</b>\n\n"
            "Отправь мне своё резюме в формате <b>PDF</b>,\n"
            "и я проанализирую его с помощью AI.\n\n"
            "✨ <b>Что я оценю:</b>\n"
            "• Сильные стороны\n"
            "• Области для улучшения\n"
            "• Рекомендации по доработке\n"
            "• Актуальные навыки для рынка\n"
            "• Конкурентоспособность\n\n"
            "📎 Жду PDF-файл..."
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()