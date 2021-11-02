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
HOMEWORK_STATUSES_URL = ('https://practicum.yandex.ru/'
                         'api/user_api/homework_statuses/')
UNEXPECTED_STATUS = ('Обнаружен неожиданный статус: \"{status}\"')
PROJECT_CHECKED = ('У вас проверили работу \"{name}\"!\n\n{verdict}')

VERDICTS = {'reviewing': 'Проект находится на ревью.',
            'rejected': 'К сожалению, в работе нашлись ошибки.',
            'approved': 'Ревьюеру всё понравилось, работа зачтена!'}
CONNECTION_ERROR_MESSAGE = (
    'При выполнении запроса произошла ошибка: \"{error}\".\n'
    'url: \"{homework_statuses_url}\"\n'
    'headers: \"{headers}\"\n'
    'params: \"{params}\"'
)
LOGGING_MESSAGE_ERROR = ('Не удалось выполнить итерацию. Ошибка: \"{error}\".')


def __parse_homework_status(homework):
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


def __get_homeworks(current_timestamp):
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


def __send_message(message):
    return Bot(token=TELEGRAM_TOKEN).send_message(CHAT_ID, message)


def main():
    '''Main entry point'''
    timestamp = 0
    while True:
        try:
            homeworks_statuses = __get_homeworks(timestamp)
            if 'homeworks' in homeworks_statuses:
                homeworks = homeworks_statuses['homeworks']
                if len(homeworks) > 0:
                    message = __parse_homework_status(homeworks[0])
                    __send_message(message)
            timestamp = int(time.time())
            time.sleep(30 * 60)

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
