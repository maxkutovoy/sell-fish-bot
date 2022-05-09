#!/usr/bin/env python

from environs import Env
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, ReplyKeyboardRemove, Update, chat)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from telegram.utils import helpers
import requests


def start_tgbot(tg_token):
    def handle(self, *args, **options):

        updater = Updater(token=tg_token)

        dispatcher = updater.dispatcher

        conversation = ConversationHandler(
            entry_points=[CommandHandler('  ', start_handler)],
            states={
                'callback_create_game': [
                    CallbackQueryHandler(
                        callback_create_game
                    )
                ],
                'join_the_game': [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        join_the_game
                    )
                ],
                'get_game_name': [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        get_game_name
                    )
                ],
                'callback_cost_gift': [
                    CallbackQueryHandler(
                        callback_cost_gift
                    )
                ],
                'callback_registration_period': [
                    CallbackQueryHandler(
                        callback_registration_period
                    )
                ],
                'get_dispatch_date': [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        get_dispatch_date
                    )
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conversation)

        updater.start_polling()
        updater.idle()


def start(bot, update):
    pass




def main():
    env = Env()
    env.read_env()

    tg_token = env.str('TG_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')
    moltin_token = env.str('MOLTIN_TOKEN')

    headers = {"Authorization": f"Bearer {moltin_token}"}





if __name__ == '__main__':
    main()