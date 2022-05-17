#!/usr/bin/env python
import os
import random
from pprint import pprint

import requests
from environs import Env


def get_moltin_token(moltin_client_id, client_secret):
    data = {
        'client_id': moltin_client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    return response.json()['access_token']


def get_all_products(moltin_token):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.get('https://api.moltin.com/v2/products', headers=headers)
    return response.json()


def get_product_info(moltin_token, product_id):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}', headers=headers)
    return response.json()


def add_new_product(moltin_token):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    json_data = {
        'data': {
            'type': 'product',
            'name': 'Forel',
            'slug': 'Forel',
            'sku': '002',
            'description': 'delicious trout',
            'manage_stock': True,
            'price': [
                {
                    'amount': 100,
                    'currency': 'USD',
                    'includes_tax': True,
                },
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }

    response = requests.post('https://api.moltin.com/v2/products', headers=headers, json=json_data)
    print(response.status_code)


def add_product_to_cart(moltin_token):
    products = get_all_products(moltin_token)
    pprint(products)
    products_ids = [product['id'] for product in products['data']]
    print(products_ids)
    random_product = random.choice(products_ids)
    print(random_product)

    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    json_data = {
        'data': {
            'id': 'ca7118ee-3468-4c74-b07f-3ffb7fae694d',
            'type': 'cart_item',
            'quantity': 1,
        },
    }

    response = requests.post('https://api.moltin.com/v2/carts/mycart/items', headers=headers, json=json_data)
    print(response.status_code)
    pprint(response.json())


def get_users_cart(moltin_token):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.get('https://api.moltin.com/v2/carts/mycart', headers=headers)
    pprint(response.json())


def clean_up_the_cart(moltin_token):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.delete('https://api.moltin.com/v2/carts/mycart', headers=headers)
    print(response.status_code)


def get_file(moltin_token, file_id, media_dir='media'):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/files/{file_id}', headers=headers)
    response.raise_for_status()
    file_info = response.json()
    filename = os.path.join(media_dir, file_info['data']['file_name'])
    file_url = file_info['data']['link']['href']

    response = requests.get(file_url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)

    return filename


def main():
    pass


if __name__ == '__main__':
    env = Env()
    env.read_env()

    moltin_client_id = env.str('MOLTIN_CLIENT_ID')
    moltin_token = env.str('MOLTIN_TOKEN')
    moltin_client_secret = env.str('MOLTIN_CLIENT_SECRET')
    # get_moltin_token(moltin_client_id, moltin_client_secret)
    # add_new_product(moltin_token)
    # get_all_products(moltin_token)
    # add_product_to_cart(moltin_token)
    # get_users_cart(moltin_token)
    # clean_up_the_cart(moltin_token)
