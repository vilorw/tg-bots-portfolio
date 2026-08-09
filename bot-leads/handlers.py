import re
import logging
from typing import Optional
from telegram import Update, User, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from config import config, Limits
from texts import Texts, inline_cancel, reply_contact, inline_comment_skip, inline_confirm

logger = logging.getLogger(__name__)

# FSM States
NAME, PHONE, COMMENT, PREVIEW = range(4)

def format_phone(phone: str) -> Optional[str]:
    """Форматирует номер. Возвращает None, если невалиден."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 11 and (digits.startswith("7") or digits.startswith("8") or phone.startswith("+")):
        return f"+{digits}" if phone.startswith("+") else f"+7{digits[1:]}"
    return None

async def start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    text = Texts.START.format(progress=Texts.progress(1))
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=inline_cancel())
    else:
        # Убираем возможную залипшую Reply-клавиатуру при старте
        await update.message.reply_text("🔄 Инициализация...", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=inline_cancel())
    return NAME

async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    
    if not (Limits.NAME_MIN <= len(name) <= Limits.NAME_MAX) or any(char.isdigit() for char in name):
        await update.message.reply_text("❌ Введите настоящее имя (без цифр).", reply_markup=inline_cancel())
        return NAME
    
    context.user_data["name"] = name
    # Отправляем REPLY клавиатуру для запроса контакта
    await update.message.reply_text(
        Texts.ask_phone(name), 
        parse_mode="HTML", 
        reply_markup=reply_contact()
    )
    return PHONE

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Проверка: если юзер нажал кнопку "❌ Отмена" на Reply-клавиатуре
    if update.message.text == "❌ Отмена":
        return await cancel_dialog_text(update, context)

    # Получаем телефон либо из объекта contact, либо из текста
    if update.message.contact:
        raw_phone = update.message.contact.phone_number
    else:
        raw_phone = update.message.text.strip()

    formatted_phone = format_phone(raw_phone)
    if not formatted_phone:
        await update.message.reply_text("❌ Неверный формат. Попробуйте еще раз.")
        return PHONE
    
    context.user_data["phone"] = formatted_phone
    
    text = (
        f"✅ Номер сохранён: {formatted_phone}\n\n"
        f"{Texts.progress(3)} <i>Шаг 3 из 4</i>\n\n"
        f"💬 <b>Комментарий к заявке</b> (необязательно):"
    )
    # ОЧЕНЬ ВАЖНО: Удаляем Reply-клавиатуру контакта и вешаем Inline-кнопки
    msg = await update.message.reply_text("Обработка...", reply_markup=ReplyKeyboardRemove())
    await msg.delete() # Удаляем техническое сообщение
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=inline_comment_skip())
    return COMMENT

async def process_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["comment"] = "Не указан"
    else:
        comment = update.message.text.strip()
        if len(comment) > Limits.COMMENT_MAX:
            await update.message.reply_text(f"❌ Слишком длинно (макс {Limits.COMMENT_MAX}).", reply_markup=inline_cancel())
            return COMMENT
        context.user_data["comment"] = comment

    return await show_preview(update, context)

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data
    text = (
        f"📋 <b>Проверьте заявку:</b>\n\n"
        f"👤 <b>Имя:</b> {data.get('name')}\n"
        f"📞 <b>Телефон:</b> {data.get('phone')}\n"
        f"💬 <b>Комментарий:</b> {data.get('comment')}\n\n"
        f"{Texts.progress(4)} <i>Шаг 4 из 4</i>\n\n"
        f"Всё верно?"
    )
    
    msg_func = update.callback_query.edit_message_text if update.callback_query else update.message.reply_text
    await msg_func(text, parse_mode="HTML", reply_markup=inline_confirm())
    return PREVIEW

async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = context.user_data
    user: User = query.from_user
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    
    admin_text = (
        f"🚨 <b>НОВАЯ ЗАЯВКА!</b>\n\n"
        f"👤 <b>Имя:</b> {data.get('name')}\n"
        f"📞 <b>Телефон:</b> <code>{data.get('phone')}</code>\n"
        f"💬 <b>Комментарий:</b> {data.get('comment')}\n"
        f"🔗 <b>Профиль ТГ:</b> {user_link}\n"
    )
    
    try:
        await context.bot.send_message(chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}", exc_info=True)
        await query.edit_message_text("❌ <b>Ошибка сервера.</b>", parse_mode="HTML")
        return ConversationHandler.END
    
    await query.edit_message_text("✅ <b>Заявка отправлена!</b>\nМы свяжемся с вами в ближайшее время.", parse_mode="HTML")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена через Inline-кнопку"""
    context.user_data.clear()
    await update.callback_query.answer("Отменено")
    await update.callback_query.edit_message_text("❌ <b>Заявка отменена.</b> /start", parse_mode="HTML")
    return ConversationHandler.END

async def cancel_dialog_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена через текстовую команду или Reply-кнопку (удаляет клавиатуру)"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ <b>Заявка отменена.</b> /start", 
        parse_mode="HTML", 
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END