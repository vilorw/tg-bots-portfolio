from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class Texts:
    @staticmethod
    def progress(step: int, total: int = 4) -> str:
        return "🟩" * step + "⬜" * (total - step)

    START = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я помогу оставить заявку за 1 минуту.\n"
        "Менеджер свяжется с вами в ближайшее время.\n\n"
        "{progress} <i>Шаг 1 из 4</i>\n\n"
        "👉 <b>Как вас зовут?</b>"
    )

    @staticmethod
    def ask_phone(name: str) -> str:
        return (
            f"✅ Приятно познакомиться, {name}!\n\n"
            f"{Texts.progress(2)} <i>Шаг 2 из 4</i>\n\n"
            f"📱 <b>Поделитесь номером телефона:</b>\n"
            f"<i>Нажмите кнопку внизу экрана или введите вручную</i>"
        )


def inline_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить заявку", callback_data="cancel")]])

def reply_contact() -> ReplyKeyboardMarkup:
    """Нижняя клавиатура для нативного запроса контакта"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Отправить мой номер", request_contact=True)],
            [KeyboardButton("❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def inline_comment_skip() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_comment")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ])

def inline_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ])