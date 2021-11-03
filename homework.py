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
UNEXPECTED_RESPONCE_STATUS_CODE = ('Получен неожиданный код в ответе '
                                   'от сервера: \"{status_code}\".')
LOGGING_MESSAGE_ERROR = ('Не удалось выполнить итерацию. Ошибка: \"{error}\".')
EMPTY_RESPONCE_MESSAGE = 'Ответ от сервера не содержит домашние работы'


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
            UNEXPECTED_RESPONCE_STATUS_CODE.format(
                status_code=response.status_code
            )
        )
    return response.json()


def check_response(response):
    """Checking responces."""
    if 'homeworks' in response:
        homeworks = response['homeworks']
        if len(homeworks) > 0:
            homework = homeworks[0]
            return parse_status(homework)
    raise ValueError(EMPTY_RESPONCE_MESSAGE)


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
            message = check_response(homeworks_statuses)
            send_message(Bot(token=TELEGRAM_TOKEN), message)
            timestamp = int(time.time())
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
