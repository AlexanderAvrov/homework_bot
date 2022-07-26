class ServerError(Exception):
    """Исключение ошибки сервера."""


class VerdictError(Exception):
    """Исключение поиска вердикта."""


class RequestError(Exception):
    """Исключение запроса."""


class JsonError(Exception):
    """Исключение обработки ответа API."""
