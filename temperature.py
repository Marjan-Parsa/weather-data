import logging

import requests

from exc import GetTemperatureError

logger = logging.getLogger(__name__)

API_ENDPOINT = 'https://api.weatherbit.io/v2.0/history/daily?'
API_KEY = 'xxx'


def get_city_temperature_data(lat, lon, start_date, end_date):
    url = f'{API_ENDPOINT}lat={lat}&lon={lon}&start_date={start_date}&end_date={end_date}&key={API_KEY}'
    response = requests.get(url)

    if response.status_code != 200:
        logger.error('Error on getting temperature data ')
        raise GetTemperatureError('Error on getting temperature data ')

    temp_data = response.json()['data'][0]
    return temp_data['min_temp'], temp_data['max_temp']
