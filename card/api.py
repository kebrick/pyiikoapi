import requests
import json
from datetime import datetime as dt
from datetime import timedelta as td

from .exception import CheckTimeToken
from .exception import SetSession
from .exception import GetException
from .exception import PostException
from .exception import TokenException


class Auth:
    """
    Если не был присвоен кастомный session то по стандарту header будет равняться:
    {
    'Content-type': 'application/json',
    'Accept': 'application/json',
    'Content-Encoding': 'utf-8'
    }
    """
    DEFAULT_TIMEOUT = "00%3A02%3A00"

    def __init__(self, login: str, password: str, org: str, session: requests.Session = None):
        self.__session = requests.Session()
        if session is not None:
            self.__session = session
        self.__session.headers = {
            'ContentType': 'application/json',
        }
        self.__login = login
        self.__password = password
        self.__org = org
        self.__token = None
        self.__token_user = None
        self.__time_token = None
        self.__base_url = "https://iiko.biz:9900"
        self.access_token()
        # self.request_timeout = "00%3A02%3A00"

    def check_token_time(self) -> bool:
        """
        Проверка на время жизни маркера доступа
        :return: Если прошло 15 мин будет запрошен токен и метод вернёт True, иначе вернётся False
        """
        fifteen_minutes_ago = dt.now() - td(minutes=15)
        time_token = self.__time_token
        # if self.__token and self.__time_token:
        try:

            if time_token <= fifteen_minutes_ago:
                print(f"Update token: {self.access_token()}")
                return True
            else:
                return False
        except TypeError:
            raise CheckTimeToken(
                self.__class__.__qualname__,
                self.check_token_time.__name__,
                f"[ERROR] Не запрошен Token и не присвоен объект типа datetime.datetime")

    @property
    def session_s(self) -> requests.Session:
        """Вывести сессию"""
        return self.__session

    @session_s.setter
    def session_s(self, session: requests.Session = None):
        """Изменение сессии"""
        if session is None:
            raise SetSession(
                self.__class__.__qualname__,
                self.session_s.__name__,
                f"[ERROR] Не присвоен объект типа requests.Session")
        else:
            self.__session = session

    @property
    def time_token(self):
        return self.__time_token

    @property
    def login(self) -> str:
        return self.__login

    @property
    def password(self) -> str:
        return self.__password

    @property
    def org(self) -> str:
        return self.__org

    @property
    def token(self) -> str:
        return self.__token

    @property
    def token_user(self) -> str:
        return self.__token_user

    @property
    def base_url(self):
        return self.__base_url

    @base_url.setter
    def base_url(self, value: str):
        self.__base_url = value

    def access_token(self):
        """
        Получить маркер доступа апи логина
        Маркер доступа выдается на фиксированный интервал времени. По умолчанию это - 15 минут.

        """
        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/auth/access_token?user_id={self.token}&user_secret={self.password}')
            self.__token = result.text[1:-1]
            self.__time_token = dt.now()
            # return result.text[1:-1]

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")

    def echo(self, msg: str = "YUP TOKEN:)"):
        """
        Проверка маркера доступа апи логина
        :param msg: ТЕк
        """
        # /api/0/auth/echo?msg={msg}&access_token={accessToken}
        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/auth/echo?msg={msg}&access_token={self.token}')

            if result.text != msg:
                return self.access_token()

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.echo.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")

    def biz_access_token(self, biz_user_ext_app_key: str):
        """
        Получить маркер доступа пользователя biz
        """
        # /api/0/auth/biz_access_token?user_ext_id={bizUserExtAppKey}
        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/auth/biz_access_token?user_ext_id={biz_user_ext_app_key}')
            self.__token_user = result.text[1:-1]
            self.__time_token = dt.now()

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.biz_access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")

    def api_access_token(self):
        """
        Получить информацию о заданном пользователе biz, доступную для заданного апи логина

        :return: UserInfo Информация о пользователе biz из bizAccessToken, организациях, в
        которые он входит и которые могут работать с апи логином из
        apiAccessToken

        """
        # applicationMarket/userInfo?api_access_token={apiAccessToken}&biz_access_token={bizAccessToken}
        try:
            result = self.session_s.get(
                f'{self.__base_url}/applicationMarket/userInfo?api_access_token={self.token}'
                f'&biz_access_token={self.token_user}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.api_access_token.__name__,
                               f"[ERROR] Не удалось получить маркер доступа: \n{err}")


class Organization(Auth):
    """
    Все методы этого сервиса работают по протоколу https.
    Интерфейс предназначен для получения списка организаций с названиями, описаниями,
    логотипами, контактной информацией, адресом. Предполагаемый сценарий использования -
    интеграция с внешними системами, отображающими организации с доп. информацией на
    картах, в списках и т.п.
    """
    # /api/0/organization/list?access_token={accessToken}&request_timeout={requestTimeout}

    def list(self, params: dict = None):
        """
        Получение списка организаций

        :params params: {"request_timeout" : "00%3A02%3A00"}
        :return: OrganizationInfo[] Информация о организациях.
        """

        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/organization/list?access_token={self.token}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.list.__name__,
                               f"[ERROR] Не удалось получить маркер доступа: \n{err}")
