class ServerError(Exception):
    """Исключение ошибки сервера."""

    pass


class MessageError(Exception):
    """Исключение ошибки отправки сообщения."""

    pass


class VerdictError(Exception):
    """Исключение поиска вердикта."""

    pass
