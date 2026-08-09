import logging
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters, PicklePersistence

from config import config
from handlers import (
    NAME, PHONE, COMMENT, PREVIEW,
    start_dialog, process_name, process_phone, process_comment, confirm_send,
    cancel_dialog, cancel_dialog_text
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    persistence = PicklePersistence(filepath="bot_states.pickle")
    application = Application.builder().token(config.BOT_TOKEN).persistence(persistence).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_dialog)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_name)],
            # Изменение здесь: ловим либо текст, либо КОНТАКТ (для нативной кнопки)
            PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, process_phone)],
            COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_comment),
                CallbackQueryHandler(process_comment, pattern="^skip_comment$"),
            ],
            PREVIEW: [
                CallbackQueryHandler(confirm_send, pattern="^confirm$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_dialog_text),
            CommandHandler("start", start_dialog),
            CallbackQueryHandler(cancel_dialog, pattern="^cancel$"),
            MessageHandler(filters.Regex("^❌ Отмена$"), cancel_dialog_text),
        ],
        name="lead_fsm",
        persistent=True,
    )
    
    application.add_handler(conv_handler)
    logger.info("🚀 Бот запущен (Архитектура v2: Модульная)")
    application.run_polling()

if __name__ == "__main__":
    main()