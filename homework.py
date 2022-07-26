import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import JsonError, RequestError, ServerError, VerdictError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

load_dotenv()

PRACTICUM_TOKEN = os.getenv('yap_token')
TELEGRAM_TOKEN = os.getenv('bot_token')
TELEGRAM_CHAT_ID = os.getenv('T_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Метод для отправки сообщения ботом."""
    logger.debug('Бот собирается отправить сообщение')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError('Бот не смог отправить сообщение'):
        logger.error('Ошибка отправки ботом сообщения')
    else:
        logger.info('Бот отправил сообщение')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса Практикум-Домашка."""
    logger.debug('Собираемся сделать запрос к API Практикума')
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestError('Ошибка запроса к Эндпоинту'):
        logger.error('Ошибка запроса к Эндпоинту')

    if response.status_code != HTTPStatus.OK:
        message = 'API-сервиса Практикум-Домашка не отвечает'
        logger.error(message)
        raise ServerError(message)
    logger.info('Получили ответ от API Практикум-Домашка')

    try:
        response = response.json()
    except JsonError('Ошибка расшифровки ответа API'):
        logger.error('Ошибка расшифровки ответа API')

    return response


def check_response(response):
    """Проверяем ответ API на корректность."""
    logger.debug('Собираемся проверить ответ API')
    if not isinstance(response, dict):
        message = 'API-сервис выдал другой тип данных'
        logger.error(message)
        raise TypeError(message)

    if not isinstance(response['homeworks'], list):
        message = 'API-сервис выдал другой тип данных'
        logger.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        logger.error('В ответе нет ключа homeworks')
        raise Exception('В ответе нет ключа homeworks')

    try:
        return response.get('homeworks')
    except Exception("Нет ключа homeworks в ответе"):
        logger.error('Нет ключа homeworks в ответе')
    else:
        logger.debug('Передали response в функцию parse_status')


def parse_status(homework):
    """Извлекаем информацию о статусе домашней работы."""
    logger.debug('Собираемся распарсить ответ API')
    if 'homework_name' not in homework:
        message = 'Нет ключа homework_name'
        logger.error(message)
        raise KeyError(message)

    if 'status' not in homework:
        message = 'Нет ключа status'
        logger.error(message)
        raise KeyError(message)

    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = VERDICTS.get(homework_status)
    if not verdict:
        raise VerdictError('Неизвестный статус')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем доступность переменных окружения."""
    logger.debug('Проверяем доступность переменных')
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.debug('Переменные доступны')

        return True
    else:
        logger.error('Токен Практикум-Домашка или Токен бота недоступен')

        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        logger.critical('Токены или чат_ид недоступны')
        sys.exit(0)
    send_message(bot, 'Бот начал свою работу')
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) > 0:
                status = parse_status(homework[0])
                send_message(bot, status)
            else:
                logger.debug('Нет новых статусов')
                pass

            current_timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    )
    main()
