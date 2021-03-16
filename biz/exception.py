class BizException(Exception):
    pass


class TokenException(BizException):
    """Primary exception for errors thrown in the get token post request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class GetException(BizException):
    """Basic exception for errors thrown on get request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class \"{name_class}\": Method \"{name_method}\" - {message}")


class PostException(BizException):
    """Basic exception for errors thrown on post request."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class SetSession(BizException):
    """Base exception for errors caused within a get couriers."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class CheckTimeToken(BizException):
    """Base exception for errors caused within a get couriers."""

    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")


class ParamSetException(BizException):
    """"""
    def __init__(self, name_class, name_method, message):
        super().__init__(f"Class {name_class}: Method - {name_method} - {message}")