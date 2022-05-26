import logging


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, tg_chat_id):
        super().__init__()
        self.tg_bot = tg_bot
        self.tg_chat_id = tg_chat_id

    def emit(self, record):

        log_entry = self.format(record)
        self.tg_bot.send_message(
            chat_id=self.tg_chat_id,
            text=log_entry
        )
