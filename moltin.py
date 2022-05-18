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


def add_product_to_cart(moltin_token, cart_id, product_id, quantity):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        },
    }

    response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=json_data)
    response.raise_for_status()


def get_items_in_cart(moltin_token, cart_id='479351324'):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_price(moltin_token, cart_id='479351324'):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}', headers=headers)
    response.raise_for_status()
    return response.json()


def remove_item_from_cart(moltin_token, cart_id, product_id):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers=headers
    )


def clean_up_the_cart(moltin_token, cart_id):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }
    requests.delete(f'https://api.moltin.com/v2/carts/{cart_id}', headers=headers)


def create_customer(moltin_token, name, email):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }

    json_data = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        },
    }
    response = requests.post(
        'https://api.moltin.com/v2/customers',
        headers=headers,
        json=json_data
    )

    return response.json()['data']['id']


def get_file(moltin_token, file_id, media_dir):
    headers = {
        'Authorization': f'Bearer {moltin_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/files/{file_id}', headers=headers)
    response.raise_for_status()
    file_info = response.json()
    filename = file_info['data']['file_name']
    filepath = os.path.join(media_dir, file_info['data']['file_name'])

    if filename not in os.listdir(media_dir):
        file_url = file_info['data']['link']['href']
        response = requests.get(file_url)
        response.raise_for_status()

        with open(filepath, 'wb') as file:
            file.write(response.content)

    return filepath


def main():
    pass


if __name__ == '__main__':
    env = Env()
    env.read_env()

    moltin_client_id = env.str('MOLTIN_CLIENT_ID')
    moltin_client_secret = env.str('MOLTIN_CLIENT_SECRET')
    moltin_token = get_moltin_token(moltin_client_id, moltin_client_secret)

    # get_items_in_cart(moltin_token)
    get_cart_price(moltin_token)
    # get_moltin_token(moltin_client_id, moltin_client_secret)
    # add_new_product(moltin_token)
    # get_all_products(moltin_token)
    # add_product_to_cart(moltin_token)
    # get_users_cart(moltin_token)
    # clean_up_the_cart(moltin_token)
