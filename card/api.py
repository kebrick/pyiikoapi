import json
from datetime import datetime as dt
from datetime import timedelta as td

import requests

from .exception import CheckTimeToken
from .exception import GetException
from .exception import PostException
from .exception import SetSession
from .exception import TokenException
from .exception import ParamSetException


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
    BASE_URL = "https://iiko.biz"
    PORT = ":9900"

    def __init__(self, login: str, password: str, org: str, session: requests.Session = None):
        self.__session = requests.Session()
        self.__session.headers = {
            'ContentType': 'application/json',
            'Accept': 'application/json',
            'Content-Encoding': 'utf-8'
        }
        if session is not None:
            self.__session = session

        self.__login = login
        self.__password = password
        self.__org = org
        self.__token = None
        self.__token_user = None
        self.__time_token = None
        self.__base_url = f"{self.BASE_URL}{self.PORT}"
        self.access_token()

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

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")

    def echo(self, msg: str = "YUP TOKEN:)") -> bool:
        """
        Проверка маркера доступа апи логина
        :param msg: Секретное слово для проверки токена
        :return: bool True в случае соответствия и наоборот
        """
        # /api/0/auth/echo?msg={msg}&access_token={accessToken}
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/auth/echo?msg={msg}&access_token={self.token}')

            if result.text != msg:
                return False
            return True

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.echo.__name__,
                                 f"[ERROR] Не удалось проверить маркер доступа апи логина: \n{err}")

    def biz_access_token(self, biz_user_ext_app_key: str) -> str:
        """
        Получить маркер доступа пользователя biz
        """
        # /api/0/auth/biz_access_token?user_ext_id={bizUserExtAppKey}
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/auth/biz_access_token?user_ext_id={biz_user_ext_app_key}')
            self.__token_user = result.text[1:-1]
            return result.text[1:-1]
        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.biz_access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа пользователя biz: \n{err}")

    def api_access_token(self) -> json.JSONDecoder:
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

    def list(self, params: dict = None) -> json.JSONDecoder:
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

    def organization_id(self, params: dict = None) -> json.JSONDecoder:
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

    def user_organizations(self, user_id: list = None) -> json.JSONDecoder:
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

    def corporate_nutritions(self) -> json.JSONDecoder:
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
            raise GetException(self.__class__.__qualname__,
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
                f'{self.base_url}/api/0/orders/calculate_checkin_result?access_token={self.token}',
                data=order_request, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.calculate_checkin_result.__name__,
                               f"[ERROR] Не удалось рассчитать программу лояльности для заказа: \n{err}")

    def get_combos_info(self) -> json.JSONDecoder:
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
            raise GetException(self.__class__.__qualname__,
                               self.get_combos_info.__name__,
                               f"[ERROR] Не удалось получить описание всех комбо и "
                               f"категорий комбо для организации: \n{err}")

    def get_manual_condition_infos(self) -> json.JSONDecoder:
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
            raise GetException(self.__class__.__qualname__,
                               self.get_manual_condition_infos.__name__,
                               f"[ERROR] Не удалось получить ручные условия: \n{err}")

    def check_and_get_combo_price(self, get_combo_price_request: dict = None) -> json.JSONDecoder:
        """
        Проверить комбо-блюдо и рассчитать его стоимость

        :param get_combo_price_request: GetComboPriceRequest Собранное комбо-блюдо
        :return: CalculateComboPriceResult Результат проверки комбо-блюда и расчета его стоимости
        """
        # /api/0/orders/check_and_get_combo_price?access_token={accessToken}&organization={organizationId}
        if get_combo_price_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.check_and_get_combo_price.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"get_combo_price_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/orders/check_and_get_combo_price?access_token={self.token}'
                f'&organization={self.org}',
                data=get_combo_price_request, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.check_and_get_combo_price.__name__,
                                f"[ERROR] Не удалось проверить комбо-блюдо и рассчитать его стоимость: \n{err}")

    def send_sms(self, send_sms_request: dict = None) -> requests.Response:
        """
        Отправить sms-сообщение от имени ресторана
            Отправить sms с заданным текстом на заданный номер телефона от имени ресторана.

        :param send_sms_request: SendSmsRequest Запрос на отправку sms
        :return: HTTP status code in Response
        """
        # /api/0/organization/{organizationId}/send_sms?access_token={accessToken}
        if send_sms_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.send_sms.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"send_sms_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/{self.org}/send_sms?access_token={self.token}',
                data=send_sms_request)
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.send_sms.__name__,
                                f"[ERROR] Не удалось отправить sms-сообщение от имени ресторана: \n{err}")

    def send_email(self, send_email_request: dict = None) -> requests.Response:
        """
        Отправить email от имени ресторана
            Отправить email с заданными темой и текстом получателю от имени сервера.

        :param send_email_request: SendEmailRequest Запрос на отправку sms
            {"organizationId": "52F6FE1D-FC47-11E7-867A-C2306B28F5A7",
            "receiver": "test@iiko.ru","subject": "тема","body": "сообщение"}
        :return: HTTP status code in Response
        """
        # /api/0/organization/{organizationId}/send_email?access_token={accessToken}
        if send_email_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.send_email.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"send_email_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/{self.org}/send_email?access_token={self.token}',
                data=send_email_request)
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.send_email.__name__,
                                f"[ERROR] Не удалось отправить email от имени ресторана: \n{err}")

    def corporate_nutrition_report(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить ручные условия
        :param params:
            {"corporate_nutrition_id": "", "date_from": "", "date_to": ""}
        :return: CorporateNutritionReportItem[] Массив, содержащий информацию по заказам гостей
        """
        # /api/0/organization/{organizationId}/corporate_nutrition_report?corporate_nutrition_id={corporateNutritionProgramId}&date_from={dateFrom}&date_to={dateTo}&access_token={accessToken}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.corporate_nutrition_report.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        params += {"access_token": self.token}
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/organization/{self.org}/corporate_nutrition_report', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.corporate_nutrition_report.__name__,
                               f"[ERROR] Не удалось получить ручные условия: \n{err}")


class Customers(Auth):

    def get_customer_by_phone(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить данные гостя по его номеру телефона

        :param params: {"phone" : "+79999999999",} телефон пользователя
        :return: OrganizationGuestInfo Данные гостя (включая баланс)
        """
        # /api/0/customers/get_customer_by_phone?access_token={accessToken}&organization={organization}&phone={userPhone}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_customer_by_phone.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_customer_by_phone?access_token={self.token}'
                f'&organization={self.org}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_customer_by_phone.__name__,
                               f"[ERROR] Не удалось получить данные гостя по его номеру телефона: \n{err}")

    def get_customer_by_id(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить данные гостя по его идентификатору
        Получить информацию о госте организации по его уникальному идентификатору.

        :param params: {"id": "userId"} Идентификатор гостя
        :return: OrganizationGuestInfo Данные гостя (включая баланс)
        """
        # /api/0/customers/get_customer_by_id?access_token={accessToken}&organization={organization}&id={userId}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_customer_by_id.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_customer_by_id?access_token={self.token}&organization={self.org}',
                params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_customer_by_id.__name__,
                               f"[ERROR] Не удалось получить данные гостя по его идентификатору: \n{err}")

    def get_customer_by_card(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить данные гостя организации по его номеру карты
        Получить информацию о госте организации по его номеру карты внутри организации.

        :param params: {"card": "cardNumber"} Номер карты гостя
        :return: OrganizationGuestInfo Данные гостя (включая баланс)
        """
        # /api/0/customers/get_customer_by_card?access_token={accessToken}&organization={organization}&card={cardNumber}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_customer_by_card.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_customer_by_card?access_token={self.token}'
                f'&organization={self.org}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_customer_by_card.__name__,
                               f"[ERROR] Не удалось получить данные гостя по его номеру карты: \n{err}")

    def create_or_update(self, customer_for_import: dict = None) -> json.JSONDecoder:
        """
        Создать гостя или обновить информацию о госте
        Метод создает гостя, если заданного телефона нет в базе или обновляет информацию о
        госте, если такой уже есть в базе, все поля в объекте customer не обязательны, кроме
        телефона. При обновлении действует следующее правило - если какое-либо поле не указано
        в запросе на обновление, то метод не изменяет значение данного поля у гостя

        :param customer_for_import: CustomerForImport Данные пользователя (здесь поле id является обязательным)
        :return: Идентификатор гостя
        """
        # /api/0/customers/create_or_update?access_token={accessToken}&organization={organizationId}
        if customer_for_import is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_or_update.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"customer_for_import\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/create_or_update?access_token={self.token}&organization={self.org}',
                data=customer_for_import, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.create_or_update.__name__,
                                f"[ERROR] Не удалось создать гостя или обновить информацию о госте: \n{err}")

    def add_category(self, customer_id: str = None, category_id: str = None) -> requests.Response:
        """
        Добавить категорию гостю
        Добавить новую категорию гостю организации.

        :param customer_id: Идентификатор гостя
        :param category_id: Идентификатор категории, которая будет добавлена
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/add_category?access_token={accessToken}&organization={organizationId}&categoryId={categoryId}
        if customer_id is None or category_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_or_update.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: "
                                    f"\"customer_id\" или \"category_id\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/add_category?access_token={self.token}'
                f'&organization={self.org}&categoryId={category_id}')
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.add_category.__name__,
                                f"[ERROR] Не удалось добавить категорию гостю: \n{err}")

    def remove_category(self, customer_id: str = None, category_id: str = None) -> requests.Response:
        """
        Удалить категорию гостю
            Удалить категорию у гостя организации.

        :param customer_id: Идентификатор гостя
        :param category_id: Идентификатор категории, которая будет добавлена
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/remove_category?access_token={accessToken}&organization={organizationId}&categoryId={categoryId}
        if customer_id is None or category_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.remove_category.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: "
                                    f"\"customer_id\" или \"category_id\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/add_category?access_token={self.token}'
                f'&organization={self.org}&categoryId={category_id}')
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.remove_category.__name__,
                                f"[ERROR] Не удалось удалить категорию гостю: \n{err}")

    def add_card(self, customer_id: str = None, add_magnet_card_request: dict = None) -> requests.Response:
        """
        Создать новую карту гостю
            Создать новую карту и выдать ее гостю организации.

        :param customer_id: Идентификатор гостя
        :param add_magnet_card_request: Запрос на добавление новой карты гостю.
            {"cardTrack" : "123ascas","cardNumber" : "79712344567"}
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/add_card?access_token={accessToken}&organization={organizationId}
        if customer_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.add_card.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"customer_id\"")
        if add_magnet_card_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.add_card.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"add_magnet_card_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/add_card?access_token={self.token}'
                f'&organization={self.org}', data=add_magnet_card_request, )
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.add_card.__name__,
                                f"[ERROR] Не удалось создать новую карту гостю: \n{err}")

    def delete_card(self, customer_id: str = None, params: dict = None) -> requests.Response:
        """
        Удалить карту у гостя
            Удалить карту с заданным трэком у гостя организации.


        :param customer_id: Идентификатор гостя
        :param params: {"card_track" : "123ascas"} Трэк карты для удаления.
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/delete_card?access_token={accessToken}&organization={organizationId}
        if customer_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.delete_card.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"customer_id\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.delete_card.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/delete_card?access_token={self.token}'
                f'&organization={self.org}', params=params, )
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.delete_card.__name__,
                                f"[ERROR] Не удалось удалить карту у гостя: \n{err}")

    def refill_balance(self, api_change_balance_request: dict = None) -> requests.Response:
        """
       Пополнить кошелек пользователя
            Пополнить заданный кошелек пользователя для заданной организации на заданную сумму.

        :param api_change_balance_request: ApiChangeBalanceRequest Запрос на пополнения кошелька пользователя
        :return: HTTP status code in Response
        """
        # /api/0/customers/refill_balance?access_token={accessToken}
        if api_change_balance_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.refill_balance.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"api_change_balance_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/refill_balance?access_token={self.token}',
                data=api_change_balance_request, )
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.refill_balance.__name__,
                                f"[ERROR] Не удалось пополнить кошелек пользователя: \n{err}")

    def withdraw_balance(self, api_change_balance_request: dict = None) -> requests.Response:
        """
        Списать деньги с кошелька пользователя
            Пополнить заданный кошелек пользователя для заданной организации на заданную сумму.
        На сколько я понял нужно в сумме указать отрицательное значение и она будет снята с баланса пользователя.

        :param api_change_balance_request: ApiChangeBalanceRequest Запрос на пополнения кошелька пользователя
        :return: HTTP status code in Response
        """
        # /api/0/customers/withdraw_balance?access_token={accessToken}
        if api_change_balance_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.withdraw_balance.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"api_change_balance_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/withdraw_balance?access_token={self.token}',
                data=api_change_balance_request, )
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.withdraw_balance.__name__,
                                f"[ERROR] Не удалось пополнить кошелек пользователя: \n{err}")

    def add_to_nutrition_organization(self, customer_id: str, params: dict = None) -> requests.Response:
        """
        Включить гостя в программу корпоративного питания
            Включить конкретного гостя в конкретную программу корпоративного питания конкретной организации.

        :param customer_id: Идентификатор гостя
        :param params: {"corporate_nutrition_id": ""}
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/add_to_nutrition_organization?access_token={accessToken}&organization={organizationId}&corporate_nutrition_id={corporateNutritionId}
        if customer_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.add_to_nutrition_organization.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"customer_id\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.add_to_nutrition_organization.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/add_to_nutrition_organization?access_token={self.token}'
                f'&organization={self.org}', params=params)
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.add_to_nutrition_organization.__name__,
                                f"[ERROR] Не удалось включить гостя в программу корпоративного питания: \n{err}")

    def remove_from_nutrition_organization(self, customer_id: str, params: dict = None) -> requests.Response:
        """
        Исключить гостя из программы корпоративного питания
            Исключить конкретного гостя из конкретной программы корпоративного питания конкретной организации.

        :param customer_id: Идентификатор гостя
        :param params: {"corporate_nutrition_id": ""}
        :return: HTTP status code in Response
        """
        # /api/0/customers/{customerId}/remove_from_nutrition_organization?access_token={accessToken}&organization={organizationId}&corporate_nutrition_id={corporateNutritionId}
        if customer_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.remove_from_nutrition_organization.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"customer_id\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.remove_from_nutrition_organization.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/{customer_id}/remove_from_nutrition_organization?'
                f'access_token={self.token}&organization={self.org}', params=params)
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.remove_from_nutrition_organization.__name__,
                                f"[ERROR] Не удалось исключить гостя из программы корпоративного питания: \n{err}")

    def get_customers_by_organization_and_by_period(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить краткую информацию по гостям за период
            Получить краткую информацию по гостям за период, где гости были созданы или последний раз посещали ресторан.
        Примечание: размер периода ограничен 100 днями.

        :param params:
            {"dateFrom": "Дата, с которой строится отчет", "dateTo": "Дата, по которую строится отчет"}
        :return: ShortGuestInfo[] Массив, содержащий краткую информацию по гостям
        """
        # /api/0/customers/get_customers_by_organization_and_by_period?access_token={accessToken}&organization={organizationId}&dateFrom={dateFrom}&dateTo={dateTo}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_customers_by_organization_and_by_period.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()

        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_customers_by_organization_and_by_period?access_token={self.token}'
                f'&organization={self.org}', params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_customers_by_organization_and_by_period.__name__,
                               f"[ERROR] Не удалось получить краткую информацию по гостям за период: \n{err}")

    def get_categories_by_guests(self, categories_request: dict = None) -> json.JSONDecoder:
        """
        Получить категории гостей
            Получить категории гостей для запрошенных гостей.
        Примечание: количество гостей на запрос не более 200.

        :param categories_request:  CategoriesRequest Доп. информация запроса, передаваемая в body,
            и содержащая массив гостей.
        :return: GuestCategoryResult[] Массив, содержащий информацию о категориях гостей.
        """
        # /api/0/customers/get_categories_by_guests?access_token={accessToken}&organization={organizationId}
        if categories_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_categories_by_guests.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"get_categories_by_guests\"")
        self.check_token_time()

        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/get_categories_by_guests?access_token={self.token}'
                f'&organization={self.org}', data=categories_request)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.get_categories_by_guests.__name__,
                                f"[ERROR] Не удалось получить категории гостей: \n{err}")

    def get_counters_by_guests(self, counters_request: dict = None) -> json.JSONDecoder:
        """
        Получить метрики гостей (кол-во, сумму заказов)
            Получить метрики гостей для запрошенных гостей, типов метрик и периодов.
        Примечание: количество гостей на запрос не более 200.

        :param counters_request:  CountersRequest Доп. информация запроса, передаваемая в body, и содержащая массив
            гостей, типы периодов, типы метрик.
            {"guestIds": [ "03d87adc-49f5-11e8-bafa-309c2345bc0f"], "metrics": [1, 2], "periods": [0]}
        :return: GuestCounter[] Массив, содержащий метрики гостей.

        """
        # /api/0/customers/get_counters_by_guests?access_token={accessToken}&organization={organizationId}
        if counters_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_counters_by_guests.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"counters_request\"")
        self.check_token_time()

        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/get_counters_by_guests?access_token={self.token}'
                f'&organization={self.org}', data=counters_request)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.get_counters_by_guests.__name__,
                                f"[ERROR] Не удалось получить метрики гостей (кол-во, сумму заказов): \n{err}")

    def get_balances_by_guests_and_wallet(self, guest_wallets_request: dict = None,
                                          params: dict = None) -> json.JSONDecoder:
        """
        Получить балансы гостей
            Получить балансы гостей для запрошенных гостей и конкретного счета программы.
        Примечание: количество гостей на запрос не более 200.
            Идентификатор счета программы можно узнать с помощью метода получения списка активных программ.

        :param params: {"wallet": ""}
        :param guest_wallets_request:  GuestWalletsRequest  Доп. информация запроса, передаваемая в body,
            и содержащая массив гостей.
        :return: GuestBalance[] Массив, содержащий балансы гостей по конкретному счету корпитной программы.
        """
        # /api/0/customers/get_balances_by_guests_and_wallet?access_token={accessToken}&organization={organizationId}&wallet={walletId}
        if guest_wallets_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_balances_by_guests_and_wallet.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"guest_wallets_request\"")

        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_balances_by_guests_and_wallet.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()

        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/get_balances_by_guests_and_wallet?access_token={self.token}'
                f'&organization={self.org}', params=params, data=guest_wallets_request)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.get_balances_by_guests_and_wallet.__name__,
                                f"[ERROR] Не удалось получить балансы гостей: \n{err}")

    def transactions_report(self, params: dict = None, user_id: str = None):
        """
        Получить отчет по транзакциям гостей организации за период
            Получает отчет по транзакциям гостей организации за указанный период.

        :param params: {"date_from": "", "date_to": ""}
        :param user_id: Идентификатор гостя для дополнительной фильтрации (необязательный)
        :return: TransactionsReportItem[] Массив, содержащий информацию по транзакциям
            гостей организации за указанный период.
        """
        # /api/0/organization/{organizationId}/transactions_report?date_from={dateFrom}&date_to={dateTo}&access_token={accessToken}&userId={userId}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.transactions_report.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        if user_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.transactions_report.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"user_id\"")
        params += {"access_token": self.token, "userId": user_id}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_balances_by_guests_and_wallet?access_token={self.token}'
                f'&organization={self.org}', params=params, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.transactions_report.__name__,
                               f"[ERROR] Не удалось получить отчет по транзакциям гостей "
                               f"организации за период: \n{err}")

    def guest_categories(self) -> json.JSONDecoder:
        """
        Получить категории гостей по организации
            Если организация включена в сеть, будут возвращены все категории сети

        :return:GuestCategoryInfo[] Массив, содержащий категории гостей по организации.
        """
        # /api/0/customers/subscribe_on_customer_balance?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/subscribe_on_customer_balance?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.guest_categories.__name__,
                               f"[ERROR] Не удалось получить категории гостей по организации: \n{err}")

    def subscribe_on_customer_balance(self,
                                      wallet_balance_changed_subscription_request: dict = None) -> json.JSONDecoder:
        """
        Подписаться на уведомления об изменении балансов пользователей
            Создает подписку (обновляет пароль у существующей) на отправку POST-уведомлений при
            изменении балансов пользователей организации.

        При изменении баланса пользователя на url из WalletBalanceChangedSubscriptionRequest или
        GuestsChangedSubscriptionRequest отправляется POST-запрос с body в виде
        GuestChangedSubscriptionNotificationRequest с полями, относящимися к изменению баланса кошелька

        :param wallet_balance_changed_subscription_request: Доп. информация запроса,передаваемая в body, и содержащая
            информацию о создаваемой подписке.
        :return: GuestsChangedSubscriptionInfo Информация о созданной подписке
        """
        # /api/0/customers/subscribe_on_customer_balance?access_token={accessToken}&organization={organizationId}
        if wallet_balance_changed_subscription_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.subscribe_on_customer_balance.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: "
                                    f"\"wallet_balance_changed_subscription_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/subscribe_on_customer_balance?access_token={self.token}'
                f'&organization={self.org}', data=wallet_balance_changed_subscription_request)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.subscribe_on_customer_balance.__name__,
                                f"[ERROR] Не удалось подписаться на уведомления об "
                                f"изменении балансов пользователей: \n{err}")

    def unsubscribe_on_customer_balance(self, subscription_id: str = None) -> requests.Response:
        """
        Удалить подписку на уведомления об изменении балансов пользователей
            Удаляет подписку на отправку POST-уведомлений при изменении балансов пользователей организации.

        :param subscription_id: Идентификатор удаляемой подписки
        :return: HTTP status code in Response
        """
        # /api/0/customers/unsubscribe_on_customer_balance?access_token={accessToken}&subscription={subscriptionId}
        if subscription_id is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.unsubscribe_on_customer_balance.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"subscription_id\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/customers/unsubscribe_on_customer_balance?access_token={self.token}'
                f'&subscription={subscription_id}')
            return result
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.unsubscribe_on_customer_balance.__name__,
                                f"[ERROR] Не удалось удалить подписку на уведомления "
                                f"об изменении балансов пользователей: \n{err}")

    def get_subscriptions_on_customer_balance(self) -> json.JSONDecoder:
        """
        Получить все подписки об изменении баланса, созданные api-пользователем

        :return: GuestsChangedSubscriptionInfo[] Массив, содержащий информацию о подписках,
            принадлежащих api-пользователю
        """
        # /api/0/customers/get_subscriptions_on_customer_balance?access_token={accessToken}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/customers/get_subscriptions_on_customer_balance?access_token={self.token}')
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_subscriptions_on_customer_balance.__name__,
                               f"[ERROR] Не удалось получить категории гостей по организации: \n{err}")

    def create_or_update_guest_category(self, guest_category_info: dict = None) -> json.JSONDecoder:
        """
        Создать категорию гостей или обновить существующую
            Создает категорию гостей для организации или обновляет уже существующую.

        :param guest_category_info: GuestCategoryInfo  Доп. информация запроса, передаваемая в body,
            и содержащая информацию о создаваемой/обновляемой категории.
        :return: GuestCategoryInfo Информация о созданной/обновленной категории гостей
        """
        # /api/0/organization/{organizationId}/create_or_update_guest_category?access_token={accessToken}
        if guest_category_info is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_or_update_guest_category.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"guest_category_info\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/{self.org}/create_or_update_guest_category?'
                f'access_token={self.token}', data=guest_category_info)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.create_or_update_guest_category.__name__,
                                f"[ERROR] Не удалось создать категорию гостей или обновить существующую: \n{err}")

    def programs(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить программы по организации/сети

        :param params: {"network":"networkId"} Идентификатор сети (должно быть заполнено либо organizationId,
            либо networkId)
        :return: ExtendedCorporateNutritionInfo[] Информация обо всех программах организации/сети
        """
        # /api/0/organization/programs?access_token={accessToken}&organization={organizationId}&network={networkId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/organization/programs?access_token={self.token}&organization={self.org}',
                params=params)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.programs.__name__,
                               f"[ERROR] Не удалось получить программы по организации/сети: \n{err}")

    def create_marketing_campaign(self, marketing_campaign_info: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Создать маркетинговую акцию
            (метод предназначен для импорта акции, настроенной через iikobiz)

        :param marketing_campaign_info: MarketingCampaignInfo  Доп. информация запроса, передаваемая в body,
            и содержащая информацию о создаваемой маркетинговой акции.
        :param params: {"network":"networkId"} Идентификатор сети (должно быть заполнено либо organizationId,
            либо networkId)
        :return: MarketingCampaignInfo Информация о созданной акции
        """
        # /api/0/create_marketing_campaign?access_token={accessToken}&organization={organizationId}&network={networkId}
        if marketing_campaign_info is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"marketing_campaign_info\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/create_marketing_campaign?access_token={self.token}&organization={self.org}',
                params=params, data=marketing_campaign_info)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.create_marketing_campaign.__name__,
                                f"[ERROR] Не удалось создать маркетинговую акцию: \n{err}")

    def update_marketing_campaign(self, marketing_campaign_info: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Обновить маркетинговую акцию
            (метод предназначен для импорта акции, настроенной через iikobiz)

        :param marketing_campaign_info: MarketingCampaignInfo  Доп. информация запроса, передаваемая в body,
            и содержащая информацию о создаваемой маркетинговой акции.
        :param params: {"network":"networkId"} Идентификатор сети (должно быть заполнено либо organizationId,
            либо networkId)
        :return: MarketingCampaignInfo Информация о созданной акции
        """
        # /api/0/organization/update_marketing_campaign?access_token={accessToken}&organization={organizationId}&network={networkId}
        if marketing_campaign_info is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"marketing_campaign_info\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.update_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/update_marketing_campaign?access_token={self.token}&'
                f'organization={self.org}', params=params, data=marketing_campaign_info)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.update_marketing_campaign.__name__,
                                f"[ERROR] Не удалось обновить маркетинговую акцию: \n{err}")

    def create_program(self, extended_corporate_nutrition_info: dict = None, params: dict = None) -> json.JSONDecoder:
        """
       Создать программу
            (метод предназначен для импорта акции, настроенной через iikobiz)

        :param extended_corporate_nutrition_info: ExtendedCorporateNutritionInfo  Доп. информация запроса,
            передаваемая в body, и содержащая информацию о создаваемой программе.
        :param params: {"network":"networkId"} Идентификатор сети (должно быть заполнено либо organizationId,
            либо networkId)
        :return: ExtendedCorporateNutritionInfo Информация о созданной программе
        """
        # /api/0/organization/create_program?access_token={accessToken}&organization={organizationId}&network={networkId}
        if extended_corporate_nutrition_info is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.create_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"extended_corporate_nutrition_info\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.update_marketing_campaign.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/create_program?access_token={self.token}&organization={self.org}',
                params=params, data=extended_corporate_nutrition_info)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.create_program.__name__,
                                f"[ERROR] Не удалось создать программу: \n{err}")

    def update_program(self, extended_corporate_nutrition_info: dict = None, params: dict = None) -> json.JSONDecoder:
        """
       Обновить программу
            (метод предназначен для импорта акции, настроенной через iikobiz)

        :param extended_corporate_nutrition_info: ExtendedCorporateNutritionInfo  Доп. информация запроса,
            передаваемая в body, и содержащая информацию об обновляемой программе.
        :param params: {"network":"networkId"} Идентификатор сети (должно быть заполнено либо organizationId,
            либо networkId)
        :return: ExtendedCorporateNutritionInfo Информация  об обновленной программе
        """
        # /api/0/organization/update_program?access_token={accessToken}&organization={organizationId}&network={networkId}
        if extended_corporate_nutrition_info is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.update_program.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"extended_corporate_nutrition_info\"")
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.update_program.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/organization/update_program?access_token={self.token}&organization={self.org}',
                params=params, data=extended_corporate_nutrition_info)
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(self.__class__.__qualname__,
                                self.update_program.__name__,
                                f"[ERROR] Не удалось обновить программу: \n{err}")


class MobileIikoCard5(Auth):
    """Мобильное приложение iikoCard5"""
    pass


class CardService(Organization, Customers, MobileIikoCard5):
    pass
