from datetime import datetime as dt
from datetime import timedelta as td

import requests

from .exception import CheckTimeToken
from .exception import GetException
from .exception import PostException
from .exception import SetSession
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
                f'{self.base_url}/api/0/auth/access_token?user_id={self.login}&user_secret={self.password}')
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
                f'{self.base_url}/api/0/auth/echo?msg={msg}&access_token={self.token}')

            if result.text != msg:
                return self.access_token()

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.echo.__name__,
                                 f"[ERROR] Не удалось проверить маркер доступа апи логина: \n{err}")

    def biz_access_token(self, biz_user_ext_app_key: str):
        """
        Получить маркер доступа пользователя biz
        """
        # /api/0/auth/biz_access_token?user_ext_id={bizUserExtAppKey}
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/auth/biz_access_token?user_ext_id={biz_user_ext_app_key}')
            self.__token_user = result.text[1:-1]
            self.__time_token = dt.now()

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.biz_access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа пользователя biz: \n{err}")

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
                f'{self.base_url}/applicationMarket/userInfo?api_access_token={self.token}'
                f'&biz_access_token={self.token_user}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.api_access_token.__name__,
                               f"[ERROR] Не удалось получить информацию о заданном пользователе biz, "
                               f"доступную для заданного апи логина: \n{err}")


class Organization(Auth):
    """
    Все методы этого сервиса работают по протоколу https.
    Интерфейс предназначен для получения списка организаций с названиями, описаниями,
    логотипами, контактной информацией, адресом. Предполагаемый сценарий использования -
    интеграция с внешними системами, отображающими организации с доп. информацией на
    картах, в списках и т.п.
    """

    def list(self, params: dict = None):
        """
        Получение списка организаций

        :params params: {"request_timeout" : "00%3A02%3A00"}
        :return: OrganizationInfo[] Информация о организациях.
        """
        # /api/0/organization/list?access_token={accessToken}&request_timeout={requestTimeout}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/organization/list?access_token={self.token}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.list.__name__,
                               f"[ERROR] Не удалось получить маркер доступа: \n{err}")

    def organization_id(self, params: dict = None):
        """
        Получение информации о заданной организации
        Возвращает поля-описатели организации

        :param params: {"request_timeout" : "00%3A02%3A00",}
        :return: OrganizationInfo Информация о организации
        """
        # /api/0/organization/organizationId?access_token={accessToken}&request_timeout={requestTimeout}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/organization/organizationId?access_token={self.token}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.organization_id.__name__,
                               f"[ERROR] Не удалось получить информации о заданной организации: \n{err}")

    def user_organizations(self, user_id: list = None):
        """
        Получить списки организаций, доступных пользователям приложения

        :param user_id: Список идентификаторов пользователей
        :return: UserOrganizations[] Информация о организации
        """
        # applicationMarket/usersOrganizations?api_access_token={apiAccessToken}
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}applicationMarket/usersOrganizations?api_access_token={self.token}', data=user_id)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.user_organizations.__name__,
                                f"[ERROR] Не удалось получить списки организаций, "
                                f"доступных пользователям приложения: \n{err}")

    def corporate_nutritions(self):
        """
        Получить список активных программ корпоративного питания для организации

        :return: CorporateNutritionInfo[] Список активных программ корпоративного питания для организации
        """
        # /api/0/organization/{organizationId}/corporate_nutritions?access_token={accessToken}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/organization/{self.org}/corporate_nutritions?access_token={self.token}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.corporate_nutritions.__name__,
                                f"[ERROR] Не удалось получить список активных программ "
                                f"корпоративного питания для организации: \n{err}")

    def calculate_checkin_result(self, order_request: dict = None):
        """
        Рассчитать программу лояльности для заказа

        :param order_request: OrderRequest Запрос на создание заказа, по которому надо
            рассчитать применение программы лояльности. (POST-параметр. передается в body)
        :return: CheckinResult Программа лояльности заказа
        """
        # /api/0/orders/calculate_checkin_result?access_token={accessToken}
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/orders/calculate_checkin_result?access_token={self.token}', data=order_request,)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.calculate_checkin_result.__name__,
                                f"[ERROR] Не удалось рассчитать программу лояльности для заказа: \n{err}")

    def get_combos_info(self):
        """
        Получить описание всех комбо и категорий комбо для организации

        :return: CombosInfo Описание всех комбо и категорий комбо
        """
        # /api/0/orders/get_combos_info?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/get_combos_info?access_token={self.token}&organization={self.org}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.get_combos_info.__name__,
                                f"[ERROR] Не удалось получить описание всех комбо и "
                                f"категорий комбо для организации: \n{err}")

    def get_manual_condition_infos(self):
        """
        Получить ручные условия

        :return: ManualConditionInfo  Список ручных условий, которые можно будет применить к заказу
        """
        # /api/0/orders/get_manual_condition_infos?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/get_manual_condition_infos?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.get_manual_condition_infos.__name__,
                                f"[ERROR] Не удалось получить ручные условия: \n{err}")

    def check_and_get_combo_price(self, get_combo_price_request: dict = None):
        """
        Проверить комбо-блюдо и рассчитать его стоимость

        :param get_combo_price_request: GetComboPriceRequest Собранное комбо-блюдо
        :return: CalculateComboPriceResult Результат проверки комбо-блюда и расчета его стоимости
        """
        # /api/0/orders/check_and_get_combo_price?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/orders/check_and_get_combo_price?access_token={self.token}'
                f'&organization={self.org}',
                data=get_combo_price_request,)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.check_and_get_combo_price.__name__,
                                f"[ERROR] Не удалось проверить комбо-блюдо и рассчитать его стоимость: \n{err}")





class Card(Organization):
    pass
