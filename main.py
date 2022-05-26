#!/usr/bin/env python

import logging
from pathlib import Path
from textwrap import dedent

import redis
import requests
import telegram
from environs import Env
from validate_email import validate_email
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Filters, Updater, CommandHandler, MessageHandler,
                          ConversationHandler, CallbackQueryHandler)

from moltin import (get_all_products, get_product_info, get_moltin_token,
                    get_file, add_product_to_cart,
                    get_items_in_cart, get_cart_price, remove_item_from_cart,
                    clean_up_the_cart, create_customer)

import log_handler
logger = logging.getLogger('TG logger')


def generate_cart_message(items):
    answer = ''
    keyboard = []

    for item in items:
        answer += f'''\
            Название {item["name"]}
            Описание: {item["description"]}
            Цена: {item["meta"]["display_price"]["with_tax"]["unit"]["formatted"]}/кг.
            
            В корзине: {item["quantity"]} кг. на сумму {item["meta"]["display_price"]["with_tax"]["value"]["formatted"]}
            
        '''

        keyboard.append([InlineKeyboardButton(
            f'Удалить {item["name"]}',
            callback_data=f'remove:{item["id"]}'
        )])

    return dedent(answer), keyboard


def start(update, context):
    moltin_token = get_moltin_token(
        context.bot_data['moltin_client_id'],
        context.bot_data['moltin_client_secret']
    )
    all_products = get_all_products(moltin_token)

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in all_products['data']
    ]
    keyboard.append([InlineKeyboardButton("Корзина", callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Выбери продукт:', reply_markup=reply_markup)

    return 'main_menu'


def run_main_menu_handler(update, context):
    moltin_token = get_moltin_token(
        context.bot_data['moltin_client_id'],
        context.bot_data['moltin_client_secret']
    )
    query = update.callback_query

    all_products = get_all_products(moltin_token)

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in all_products['data']
    ]
    keyboard.append([InlineKeyboardButton("Корзина", callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        text='Выбери продукт:',
        chat_id=query.message.chat_id,
        reply_markup=reply_markup
    )

    return 'main_menu'


def run_about_product_handler(update, context):
    moltin_token = get_moltin_token(
        context.bot_data['moltin_client_id'],
        context.bot_data['moltin_client_secret']
    )
    query = update.callback_query
    query_data = query.data
    context.bot.answer_callback_query(update.callback_query.id)

    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data='1'),
            InlineKeyboardButton("5 кг", callback_data='5'),
            InlineKeyboardButton("10 кг", callback_data='10'),
        ],
        [InlineKeyboardButton("К продуктам", callback_data='main_menu')],
        [InlineKeyboardButton("Корзина", callback_data='cart')]
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

    answer = dedent(f"""\
        Название: {product_info['data']['name']}
        
        Описание: {product_info['data']['description']}
        
        Цена: {product_info['data']['meta']['display_price']['with_tax']['formatted']}
        """
    )
    image_id = product_info['data']['relationships']['main_image']['data'][
        'id']

    media_dir = 'media'
    Path(media_dir).mkdir(parents=True, exist_ok=True)

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

    return 'main_menu'


def get_cart(update, context):
    moltin_token = get_moltin_token(
        context.bot_data['moltin_client_id'],
        context.bot_data['moltin_client_secret']
    )
    query = update.callback_query
    chat_id = query.message.chat_id

    cart_items = get_items_in_cart(moltin_token, chat_id)
    cart_price = get_cart_price(moltin_token, chat_id)

    answer, keyboard = generate_cart_message(cart_items['data'])
    answer += f"Всего товаров на {cart_price['data']['meta']['display_price']['with_tax']['formatted']}\n\n\n"
    keyboard.append(
        [InlineKeyboardButton("К продуктам", callback_data='main_menu')],
    )
    keyboard.append(
        [InlineKeyboardButton("Оплата", callback_data='payment')],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        text=answer,
        chat_id=chat_id,
        reply_markup=reply_markup,
    )


def remove_product_from_cart(update, context):
    moltin_token = get_moltin_token(
        context.bot_data['moltin_client_id'],
        context.bot_data['moltin_client_secret']
    )

    query = update.callback_query
    product_id = query.data.split(':')[1]
    chat_id = query.message.chat_id

    remove_item_from_cart(moltin_token, chat_id, product_id)

    cart_items = get_items_in_cart(moltin_token, chat_id)
    cart_price = get_cart_price(moltin_token, chat_id)

    answer, keyboard = generate_cart_message(cart_items['data'])
    answer += f"Всего товаров на {cart_price['data']['meta']['display_price']['with_tax']['formatted']}\n\n\n"
    keyboard.append(
        [InlineKeyboardButton("К продуктам", callback_data='main_menu')]
    )
    keyboard.append(
        [InlineKeyboardButton("Оплата", callback_data='waiting_email')],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    answer += f"Всего товаров на сумму {cart_price['data']['meta']['display_price']['with_tax']['formatted']}\n\n\n"

    context.bot.send_message(
        text=answer,
        chat_id=chat_id,
        reply_markup=reply_markup,
    )
    return 'main_menu'


def waiting_email(update, context):
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id

        context.bot.send_message(
            text='Укажите ваш e-mail',
            chat_id=chat_id,
        )

        return 'main_menu'

    elif update.message:
        moltin_token = get_moltin_token(
            context.bot_data['moltin_client_id'],
            context.bot_data['moltin_client_secret']
        )
        keyboard = [
            [InlineKeyboardButton("К продуктам", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        chat_id = update.message.chat_id
        name = update.message.chat.username or update.message.chat.first_name
        email = update.message.text

        if not validate_email(email):
            answer = 'Неправильный e-mail. Напишите еще раз'
            update.message.reply_text(answer)
            return 'main_menu'

        answer = 'Заказ оформлен, с вами свяжется наш менеджер'
        update.message.reply_text(answer, reply_markup=reply_markup)

        create_customer_response = create_customer(moltin_token, name, email)
        context.user_data['moltin_customer_id'] = \
        create_customer_response['data']['id']

        clean_up_the_cart(moltin_token, cart_id=chat_id)


def help(update, context):
    update.message.reply_text("Use /start to test this bot.")


def cancel(update, context):
    return ConversationHandler.END


def log_error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def start_tg_bot(tg_token, moltin_client_id, moltin_client_secret):
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['moltin_client_id'] = moltin_client_id
    dispatcher.bot_data['moltin_client_secret'] = moltin_client_secret

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'main_menu': [
                CallbackQueryHandler(run_main_menu_handler, pattern='main_menu'),
                CallbackQueryHandler(get_cart, pattern='cart'),
                CallbackQueryHandler(remove_product_from_cart,
                                     pattern='remove*'),
                CallbackQueryHandler(waiting_email, pattern='payment'),
                CallbackQueryHandler(run_about_product_handler),
                MessageHandler(Filters.text, waiting_email)
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
    tg_chat_id = env.str('TG_CHAT_ID')
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

    tg_bot = telegram.Bot(token=tg_token)
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_handler.TelegramLogsHandler(tg_bot, tg_chat_id))

    try:
        start_tg_bot(tg_token, moltin_client_id, moltin_client_secret)
    except requests.exceptions.HTTPError as error:
        logger.warning('Проблема с Телеграм-ботом')
