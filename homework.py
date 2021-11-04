import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
RETRY_TIME = 300
HOMEWORK_STATUSES_URL = ('https://practicum.yandex.ru/'
                         'api/user_api/homework_statuses/')
UNEXPECTED_STATUS = ('Обнаружен неожиданный статус: \"{status}\"')
PROJECT_CHECKED = ('Изменился статус проверки работы \"{name}\"!\n\n{verdict}')

VERDICTS = {'reviewing': 'Работа взята на проверку ревьюером.',
            'rejected': 'Работа проверена, в ней нашлись ошибки.',
            'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!'}
CONNECTION_ERROR_MESSAGE = (
    'При выполнении запроса произошла ошибка: \"{error}\".\n'
    'url: \"{url}\"\n'
    'headers: \"{headers}\"\n'
    'params: \"{params}\"'
)
UNEXPECTED_RESPONSE_STATUS_CODE = (
    'Получен неожиданный код в ответе от сервера: \"{status_code}\".\n'
    'url: \"{url}\"\n'
    'headers: \"{headers}\"\n'
    'params: \"{params}\"')
ERROR_RESPONSE_JSON_KEY = (
    'В ответе от сервера найдена ошибка с ключём: \"{key}\".\n'
    'значение: \"{value}\".\n'
    'url: \"{url}\"\n'
    'headers: \"{headers}\"\n'
    'params: \"{params}\"')
LOGGING_MESSAGE_ERROR = ('Не удалось выполнить итерацию. Ошибка: \"{error}\".')
EMPTY_RESPONSE_MESSAGE = 'Ответ от сервера не содержит домашние работы'


def parse_status(homework):
    """Parsing servers answer."""
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(
            UNEXPECTED_STATUS.format(
                status=status
            )
        )
    return PROJECT_CHECKED.format(
        verdict=VERDICTS[status],
        name=homework['homework_name']
    )


def get_api_answer(url, current_timestamp):
    """Getting statuses from the server."""
    headers = HEADERS
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=url,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            CONNECTION_ERROR_MESSAGE.format(
                error=error,
                url=url,
                headers=headers,
                params=params
            )
        )
    if response.status_code != 200:
        raise ConnectionError(
            UNEXPECTED_RESPONSE_STATUS_CODE.format(
                status_code=response.status_code,
                url=url,
                headers=headers,
                params=params
            )
        )
    json = response.json()
    json_error_keys = ['error', 'code']
    for key in json_error_keys:
        if key in json:
            raise ValueError(
                ERROR_RESPONSE_JSON_KEY.format(
                    key=key,
                    value=json[key],
                    url=url,
                    headers=headers,
                    params=params
                )
            )
    return json


def check_response(response):
    """Checking RESPONSEs."""
    if 'homeworks' not in response:
        raise ValueError(EMPTY_RESPONSE_MESSAGE)
    homeworks = response['homeworks']
    if len(homeworks) == 0:
        raise ValueError(EMPTY_RESPONSE_MESSAGE)
    return parse_status(homeworks[0]), response['current_date']


def send_message(bot, message):
    """Sending a message via telegram."""
    return bot.send_message(CHAT_ID, message)


def main():
    """Main entry point."""
    timestamp = 0
    while True:
        try:
            homeworks_statuses = get_api_answer(
                HOMEWORK_STATUSES_URL,
                timestamp
            )
            message, timestamp = check_response(homeworks_statuses)
            print(message)
            print(timestamp)
            send_message(Bot(token=TELEGRAM_TOKEN), message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            logging.error(
                msg=LOGGING_MESSAGE_ERROR.format(
                    error=error
                ),
                exc_info=True
            )
            time.sleep(30)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
