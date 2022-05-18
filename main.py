#!/usr/bin/env python

import logging
from pprint import pprint

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, Updater, CommandHandler, CallbackQueryHandler, ConversationHandler

from moltin import get_all_products, get_product_info, get_moltin_token, get_file, add_product_to_cart


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)


def start(update, context):
    moltin_token = context.bot_data['moltin_token']
    all_products = get_all_products(moltin_token)
    chat_id = update.message.chat.id,
    message_id = update.message.message_id
    context.bot_data[chat_id] = 'main_menu'

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in all_products['data']
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выбери рыбу', reply_markup=reply_markup)

    return 'main_menu'


def main_menu(update, context):
    moltin_token = context.bot_data['moltin_token']
    query = update.callback_query
    chat_id = query.message.chat_id,

    context.bot_data[chat_id] = 'main_menu'
    all_products = get_all_products(moltin_token)

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in all_products['data']
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        text='Выбери продукт:',
        chat_id=query.message.chat_id,
        reply_markup=reply_markup
    )
    # context.bot.editMessageText(
    #     text='Выбери рыбу',
    #     chat_id=query.message.chat_id,
    #     message_id=query.message.message_id,
    #     reply_markup=reply_markup
    # )
    db.set(f'{query.message.chat_id}', 'main_menu')
    return 'main_menu'


def about_product(update, context):
    query = update.callback_query
    query_data = query.data

    moltin_token = context.bot_data['moltin_token']
    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data='1'),
            InlineKeyboardButton("5 кг", callback_data='5'),
            InlineKeyboardButton("10 кг", callback_data='10'),
        ],
        [InlineKeyboardButton("К продуктам", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query_data.isdigit():
        context.bot.answer_callback_query(update.callback_query.id)

        add_product_to_cart(
            moltin_token=moltin_token,
            cart_id=query.message.chat_id,
            product_id=context.user_data['current_product_id'],
            quantity=int(query_data)
        )

        context.bot.send_message(
            text=f"Товар {context.user_data['current_product_name']} - {query_data} кг - добавлен в корзину.",
            chat_id=query.message.chat_id,
        )
        query_data = context.user_data['current_product_id']

    product_info = get_product_info(moltin_token, query_data)
    context.user_data['current_product_id'] = query_data
    context.user_data['current_product_name'] = product_info['data']['name']

    # pprint(product_info)
    answer = (
        f"Название: {product_info['data']['name']}\n\n"
        f"Описание: {product_info['data']['description']}\n\n"
        f"Цена: {product_info['data']['meta']['display_price']['with_tax']['formatted']}"
    )
    image_id = product_info['data']['relationships']['main_image']['data']['id']

    media_dir = 'media'

    filename = get_file(moltin_token, image_id, media_dir)

    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(filename, 'rb'),
        caption=answer,
        reply_markup=reply_markup
    )
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    # update.message.reply_text(answer, reply_markup=reply_markup)
    # context.bot.editMessageText(
    #     text=answer,
    #     chat_id=query.message.chat_id,
    #     message_id=query.message.message_id,
    #     reply_markup=reply_markup
    # )
    # print(query.message.chat_id)
    db.set(f'{query.message.chat_id}', 'about_product')
    return 'main_menu'


def help(update, context):
    update.message.reply_text("Use /start to test this bot.")


def cancel(update, context):
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def start_tg_bot(tg_token, moltin_client_id, moltin_client_secret):
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['moltin_token'] = get_moltin_token(moltin_client_id, moltin_client_secret)

    # dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(CallbackQueryHandler(callback_menu))
    # dispatcher.add_handler(CommandHandler('help', help))
    # dispatcher.add_error_handler(error)

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'main_menu': [
                CallbackQueryHandler(main_menu, pattern='main_menu'),
                CallbackQueryHandler(about_product)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conversation)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    tg_token = env.str('TG_TOKEN')
    moltin_client_id = env.str('MOLTIN_CLIENT_ID')
    moltin_client_secret = env.str('MOLTIN_CLIENT_SECRET')

    redis_host = env.str('REDIS_DB_NAME')
    redis_port = env.int('REDIS_PORT')
    redis_pass = env.str('REDIS_PASSWORD')

    db = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=0
    )

    start_tg_bot(tg_token, moltin_client_id, moltin_client_secret)