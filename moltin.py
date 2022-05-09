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
    print(response.text)


def main():
    env = Env()
    env.read_env()

    moltin_client_id = env.str('MOLTIN_CLIENT_ID')
    moltin_token = env.str('MOLTIN_TOKEN')
    moltin_client_secret = env.str('MOLTIN_CLIENT_SECRET')

    get_moltin_token(moltin_client_id, moltin_client_secret)


if __name__ == '__main__':
    pass
