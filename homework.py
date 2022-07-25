import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import ServerError, MessageError, VerdictError

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


PRACTICUM_TOKEN = os.getenv('yap_token')
TELEGRAM_TOKEN = os.getenv('bot_token')
TELEGRAM_CHAT_ID = 107441279

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Метод для отправки сообщения ботом"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except MessageError('Бот не смог отправить сообщение'):
        logger.error('Ошибка отправки ботом сообщения')
    else:
        logger.info('Бот отправил сообщение')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса Практикум-Домашка"""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        logger.error('API-сервиса Практикум-Домашка не отвечает')
        raise ServerError('API-сервиса Практикум-Домашка не отвечает')
        return None
    logger.info('Получили ответ от API Практикум-Домашка')
    return response.json()


def check_response(response):
    """Проверяем ответ API на корректность"""
    if type(response['homeworks']) != list:
        logger.error('API-сервис выдал другой тип данных')
        raise Exception('API-сервис выдал другой тип данных')
    if type(response) != dict:
        logger.error('API-сервис выдал другой тип данных')
        raise Exception('API-сервис выдал другой тип данных')
    try:
        return response.get('homeworks')
    except Exception("API-сервис не отвечает"):
        logger.error('API-сервис не отвечает')
    else:
        logger.debug('Передали response в функцию parse_status')


def parse_status(homework):
    """Извлекаем информацию о статусе домашней работы"""
    if 'homework_name' not in homework:
        logger.error('Нет ключа homework_name')
        raise KeyError('Нет ключа homework_name')
    if 'status' not in homework:
        logger.error('Нет ключа status')
        raise KeyError('Нет ключа status')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        raise VerdictError('Неизвестный статус')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем доступность переменных окружения"""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN:
        return True
    else:
        logger.error('Токен Практикум-Домашка или Токен бота недоступен')
        return False


def main():
    """Основная логика работы бота"""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    check_tokens()
    while True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) > 0:
                status = parse_status(homework[0])
            else:
                status = None
            if status is not None:
                send_message(bot, status)
            else:
                pass
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
