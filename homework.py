import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
HOMEWORK_STATUSES_URL = ('https://practicum.yandex.ru/'
                         'api/user_api/homework_statuses/')
UNEXPECTED_STATUS = ('Обнаружен неожиданный статус: \"{status}\"')
PROJECT_CHECKED = ('У вас проверили работу \"{name}\"!\n\n{verdict}')

VERDICTS = {'reviewing': 'Проект находится на ревью.',
            'rejected': 'К сожалению, в работе нашлись ошибки.',
            'approved': 'Ревьюеру всё понравилось, работа зачтена!'}
CONNECTION_ERROR_MESSAGE = (
    'При выполнении запроса произошла ошибка: \"{error}\".'
    'url: \"{homework_statuses_url}\"'
    'headers: \"{headers}\"'
    'params: \"{params}\"'
)


def parse_homework_status(homework):
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


def get_homeworks(current_timestamp):
    homework_statuses_url = HOMEWORK_STATUSES_URL
    headers = HEADERS
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=homework_statuses_url,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            CONNECTION_ERROR_MESSAGE.format(
                error=error,
                homework_statuses_url=homework_statuses_url,
                headers=headers,
                params=params
            )
        )
    return response.json()


def send_message(message):
    return Bot(token=TELEGRAM_TOKEN).send_message(CHAT_ID, message)


def main():
    timestamp = 0
    while True:
        try:
            homeworks_statuses = get_homeworks(timestamp)
            if 'homeworks' in homeworks_statuses:
                homeworks = homeworks_statuses['homeworks']
                if len(homeworks) > 0:
                    message = parse_homework_status(homeworks[0])
                    send_message(message)
            timestamp = int(time.time())
            time.sleep(30 * 60)

        except Exception as error:
            logging.error(
                msg='Не удалось выполнить итерацию. '
                    f'Ошибка: {error}',
                exc_info=True
            )
            time.sleep(30)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        'my_logger.log',
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)
    main()
