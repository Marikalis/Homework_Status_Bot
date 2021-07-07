import os
import time
import logging
from logging.handlers import RotatingFileHandler
import requests

from telegram import Bot
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HW_STATUSES_URL = \
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
UNEXPECTED_STATUS = 'Статус работы неизвестен.'
PROJECT_CHECKED = ('У вас проверили работу \"{homework_name}\"!\n\n{verdict}')
HOMEWORKS_KEY = 'homeworks'

bot = Bot(token=TELEGRAM_TOKEN)

bot_dict = {'reviewing': 'Проект находится на ревью.',
            'rejected': 'К сожалению, в работе нашлись ошибки.',
            'approved': 'Ревьюеру всё понравилось, работа зачтена!'}


def parse_homework_status(homework):
    homework_status = homework['status']
    if homework_status is None or homework_status not in bot_dict:
        raise UNEXPECTED_STATUS
    verdict = bot_dict[homework_status]
    return PROJECT_CHECKED.format(
        verdict=verdict,
        homework_name=homework['homework_name']
    )


def get_homeworks(current_timestamp):
    homework_statuses_url = HW_STATUSES_URL
    headers = HEADERS
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(
            homework_statuses_url,
            headers=headers,
            params=payload
        ).json()
    except requests.exceptions.RequestException as error:
        raise f'Ошибка в ответе от сервера: {error}'
    except TypeError as error:
        raise f'Ошибка в при распаковке ответа от сервера: {error}'
    except ValueError as error:
        raise f'Ошибка в при распаковке ответа от сервера: {error}'
    return response


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    timestamp = int(time.time())
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
        backupCount=5)
    logger.addHandler(handler)

    while True:
        try:
            homeworks_statuses = get_homeworks(timestamp)
            if HOMEWORKS_KEY not in homeworks_statuses:
                raise UNEXPECTED_STATUS
            homeworks = homeworks_statuses[HOMEWORKS_KEY]
            if len(homeworks) > 0:
                message = parse_homework_status(homeworks[0])
            if message is not None:
                send_message(message)
            time.sleep(30 * 60)

        except Exception as error:
            logging.error(error, exc_info=True)
            time.sleep(30)


if __name__ == '__main__':
    main()
