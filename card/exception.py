class CardException(Exception):
    pass


class TokenException(CardException):
    """Primary exception for errors thrown in the get token post request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class GetException(CardException):
    """Basic exception for errors thrown on get request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class \"{name_class}\": Method \"{name_method}\" - {message}")


class PostException(CardException):
    """Basic exception for errors thrown on post request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class SetSession(CardException):
    """Base exception for errors caused within a get couriers."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class CheckTimeToken(CardException):
    """Base exception for errors caused within a get couriers."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class ParamSetException(CardException):
    """"""
    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")