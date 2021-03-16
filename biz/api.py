import requests
import json
from datetime import datetime as dt
from datetime import timedelta as td
from .exception import TokenException
from .exception import GetException
from .exception import PostException
from .exception import SetSession
from .exception import CheckTimeToken
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

    # const
    DEFAULT_TIMEOUT = "00%3A02%3A00"
    BASE_URL = "https://iiko.biz"
    PORT = ":9900"

    def __init__(self, login: str, password: str, org: str, session: requests.Session = None):
        self.__session = requests.Session()
        if session is not None:
            self.__session = session

        self.__login = login
        self.__password = password
        self.__org = org
        self.__token = None
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
    def base_url(self):
        return self.__base_url

    @base_url.setter
    def base_url(self, value: str):
        self.__base_url = value

    def access_token(self):
        """Получить маркер доступа"""
        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/auth/access_token?user_id={self.__login}&user_secret={self.__password}')
            self.__token = result.text[1:-1]
            self.__time_token = dt.now()

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.access_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")


class Orders(Auth):
    """
    Сервис для работы с разделом заказов iiko Biz Api
    Все методы возвращают чистый json
    """

    def get_courier_orders(self, params: dict = None) -> json:
        """
        Активные заказы курьера

        :param params: {"courier": "Идентификатор курьера", "request_timeout" : "00%3A02%3A00"}
        :return: DeliveryOrdersResponse Информация о заказах
        """
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_courier_orders.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/get_courier_orders?access_token={self.token}'
                f'&organization={self.org}',
                params=params)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.get_courier_orders.__name__,
                               f"[ERROR] Не удалось получить активные заказы курьера\n{err}")

    def delivery_orders(self, params: dict = None) -> json:
        """
        Получение информации о всех доставках в заданном временном интервале.

        :param params: {"dateFrom": "","dateTo" : "", "deliveryStatus" : "", "deliveryTerminalId" : "",
            "request_timeout" : "00%3A02%3A00"}
        "dateFrom" : string : Дата начала интервала (включительно).
        "dateTo" : string : Дата окончания интервала (включительно).
        "deliveryStatus" : string : Статус доставки (регистронезависимый).
        Должно принимать одно из следующих значений:
        ● NEW
        ● WAITING
        ● ON_WAY
        ● CLOSED
        ● CANCELLED
        ● DELIVERED
        ● UNCONFIRMED
        "deliveryTerminalId" : string : Идентификатор терминала доставки.
        "requestTimeout" : string : Таймаут для выполнения запроса.
        :return: DeliveryOrdersResponse Информация о заказах
        """
        # /api/0/orders/deliveryOrders?access_token={accessToken}&organization={organizationId}
        # &dateFrom={dateFrom}&dateTo={dateTo}&deliveryStatus={deliveryStatus}
        # &deliveryTerminalId={deliveryTerminalId}&request_timeout={requestTimeout}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.delivery_orders.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/deliveryOrders?access_token={self.token}&organization={self.org}',
                params=params)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(self.__class__.__qualname__,
                               self.delivery_orders.__name__,
                               f"[ERROR] Не удалось получить все заказы \n{err}")

    def set_order_delivered(self, set_order_delivered_request: dict = None, params: dict = None):
        """
        Отметить заказ доставленным или недоставленным.

        :param set_order_delivered_request: SetOrderDeliveredRequest содержимое запроса на изменение статуса доставки.
        :param params: {"request_timeout" : "00%3A02%3A00"}
        :return: http status code
        """
        # /api/0/orders/set_order_delivered?access_token={accessToken}&organization={organizationId}&request_timeout={requestTimeout}
        if set_order_delivered_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.set_order_delivered.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"set_order_delivered_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/orders/set_order_delivered?access_token={self.token}&organization='
                f'{self.org}',
                params=params,
                data=set_order_delivered_request, )
            return result.status_code

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.set_order_delivered.__name__,
                f"[ERROR] Не удалось отправить подтверждение\n{err}"
            )


class Nomenclature(Auth):
    """
    Номенклатура (меню)
    """

    def nomenclature(self) -> json:
        """
        Получить дерево номенклатуры
        Один запрос возвращает информацию как о группах, так и о продуктах.
        Метод возвращает:
        1. полное дерево продуктов,
        2. null при их отсутствии.

        :return:
        {
        groups:Группы
        products:Продукты
        revision:Ревизия (одна на все дерево продуктов)
        productCategories:Группы продуктов
        uploadDate:Дата последнего обновления меню в формате "yyyy-MM-dd HH:mm:ss"
        }
        """
        # /api/0/nomenclature/{organizationId}?access_token={accessToken}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/nomenclature/{self.org}?access_token={self.token}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.nomenclature.__name__,
                f"[ERROR] Не удалось получить список курьеров\n{err}"
            )


class Cities(Auth):
    """
    Города, улицы, регионы
    Получение списка городов и их улиц

    """

    def cities(self) -> json:
        """
        Метод возвращает список всех городов и улиц каждого из городов. Эти данные могут
        быть использовать для задания адреса доставки.

        :return: CityWithStreets[] Города с улицами
        """
        # /api/0/cities/cities?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/cities/cities?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.cities.__name__,
                f"[ERROR] Не удалось получить список городов с улицами\n{err}"
            )

    def cities_list(self):
        """
        Получение списка городов организации
        Метод возвращает список всех городов заданной организации. Эти данные могут быть
        использовать для задания адреса доставки.

        :return: City[] Города
        """
        # /api/0/cities/citiesList?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/cities/citiesList?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.cities_list.__name__,
                f"[ERROR] Не удалось получить список городов\n{err}"
            )

    def streets(self, params: dict):
        """
        Получение списка улиц города заданной организации
        Метод возвращает список всех городов заданной организации. Эти данные могут быть
        использовать для задания адреса доставки.

        :param params:  {"city": "Идентификатор города"}
        :return: Street[] Улицы
        """
        # /api/0/streets/streets?access_token={accessToken}&organization={organizationId}&city={cityId}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.streets.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/streets/streets?access_token={self.token}&organization={self.org}',
                params=params)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.streets.__name__,
                f"[ERROR] Не удалось получить список улиц\n{err}"
            )

    def regions(self):
        """
        Получение списка регионов
        Метод возвращает список всех всех регионов, которые есть в справочнике регионов организации.
        Эти данные могут быть использовать для задания региона в адресе доставки.

        :return: Region[] Список регионов
        """
        # /api/0/regions/regions?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/regions/regions?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.regions.__name__,
                f"[ERROR] Не удалось получить список регионов\n{err}"
            )


class Notices(Auth):
    """
    Уведомления
    Все методы этого сервиса работают по протоколу https.
    """

    def notices(self, notices_request: dict = None, params: dict = None) -> json:
        """
        Получить данные журнала событий


        :param notices_request: NoticesRequest информация об уведомлениях (POST-параметр. передается в body)
        :param params: {"request_timeout":""}
        :return :NoticesResponse: ответ об успешности операции отправки
        :rtype :obj:`json`
        """
        # /api/0/notices/notices?access_token={accessToken}&request_timeout={requestTimeout}
        if notices_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.notices.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"notices_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/regions/regions?access_token={self.token}&organization={self.org}',
                params=params,
                data=notices_request)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.notices.__name__,
                f"[ERROR] Не удалось получить список регионов\n{err}"
            )


class RMSSettings(Auth):
    """
    Получение списка протоколов заданной организации
    Возвращает список поддерживаемых протоколов
    """

    def supported_protocols(self) -> json:
        """
        Получение списка протоколов заданной организации

        :return: OrganizationSupportedProtocol[] :Список протоколов, поддерживаемых организацией
        """
        # /api/0/rmsSettings/supportedProtocols?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/supportedProtocols?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.supported_protocols.__name__,
                f"[ERROR] Не удалось получить список регионов\n{err}"
            )

    def get_roles(self) -> json:
        """
        :return :OrganizationRole: Список всех ролей организации Response
        """
        # /api/0/rmsSettings/getRoles?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/supportedProtocols?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_roles.__name__,
                f"[ERROR] Не удалось получить список регионов\n{err}"
            )

    def get_employees(self) -> json:
        """
        Получение списка сотрудников организации

        :return : OrganizationUser: Список всех сотрудников организации Response
        """
        # /api/0/rmsSettings/getEmployees?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getEmployees?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_employees.__name__,
                f"[ERROR] Не удалось получить список сотрудников организации\n{err}"
            )

    def get_restaurant_sections(self) -> json:
        """
        Получение списка залов организации

        :return :RestaurantSectionsResponse :Список всех залов организации
        """
        # /api/0/rmsSettings/getRestaurantSections?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getRestaurantSections?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_restaurant_sections.__name__,
                f"[ERROR] Не удалось получить список залов организации\n{err}"
            )

    def get_orders_types(self) -> json:
        """
        Получение списка допустимых типов заказов

        :return :OrderTypesResponse Справочник типов заказов
        """
        # /api/0/rmsSettings/getOrderTypes?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getOrderTypes?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_orders_types.__name__,
                f"[ERROR] Не удалось получить список допустимых типов заказов\n{err}"
            )

    def get_payment_types(self) -> json:
        """
        Получить список типов оплат

        :return PaymentType[] Внешние типы оплат
        """
        # /api/0/rmsSettings/getPaymentTypes?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getPaymentTypes?access_token={self.token}&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_payment_types.__name__,
                f"[ERROR] Не удалось получить список типов оплат\n{err}"
            )

    def get_marketing_sources(self):
        """
        Получить список маркетинговых источников

        :return: MarketingSourceInfo[] Маркетинговые источники
        """
        # /api/0/rmsSettings/getMarketingSources?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getMarketingSources?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_marketing_sources.__name__,
                f"[ERROR] Не удалось получить список типов оплат\n{err}"
            )

    def get_couriers(self) -> json:
        """
        Получить список курьеров организации

        :return: deliveryOrders:  Список курьеров организации
        :rtype: json: :obj:`json`
        """
        # /api/0/rmsSettings/getCouriers?access_token={accessToken}&organization={organizationId}

        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getCouriers?access_token={self.token}&organization={self.org}')
            return result.json()  # ['users']

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_couriers.__name__,
                f"[ERROR] Не удалось получить список курьеров организации\n{err}"
            )


class StopLists(Auth):
    """
    Все методы этого сервиса работают по протоколу https.
    """

    def get_delivery_stop_list(self) -> json:
        """
        Получить стоп-лист по сети ресторанов

        Запрос возвращает список продуктов, находящихся в стоп-листе.
        В случае запроса на колл-центра в результате могут находяится позиции стоп-листа из
        других ресторанов.

        :return: StopListAtOrganization[] Элементы стоп-листа; string[] Идентификаторы организаций, которые не
            зарегистрированы в iikoBiz.
        """
        # /api/0/stopLists/getDeliveryStopList?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/stopLists/getDeliveryStopList?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_delivery_stop_list.__name__,
                f"[ERROR] Не удалось получить стоп-лист по сети ресторанов\n{err}"
            )


class Mobile(Auth):
    """
    Мобильное приложение курьера
    """

    def signin(self, mobile_login_request_dto: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Запрос логина курьера доставки на удаленный РМС сервер

        :param mobile_login_request_dto: MobileLoginRequestDto Сущность, описывающая запрос на логин
        :param params: {"request_timeout":"00%3A02%3A00"} Таймаут для выполнения запроса
        :return: MobileLoginResultDTO, описывающий результат логина (есть ли Dto ошибки), сообщает также версию сервера
        """
        # /api/0/mobile/signin?access_token={accessToken}&request_timeout={requestTimeout}&organization={organizationId}
        if mobile_login_request_dto is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.signin.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"mobile_login_request_dto\"")
        if params is None:
            params = {"organization": self.org}
        else:
            params += {"organization": self.org}

        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/mobile/signin?access_token={self.token}',
                params=params,
                data=mobile_login_request_dto
            )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.signin.__name__,
                f"[ERROR] Не удалось получить Запрос логина курьера доставки на удаленный РМС сервер\n{err}"
            )

    def sysc(self, send_update_dto: dict = None, params: dict = None) -> json:
        """
        Запрос полной синхронизации мобильного приложения и сервера доставок
            Отсылает изменения в доставках (статус, проблема) и сохраненные gps координаты курьера.

        :param send_update_dto: Изменения доставок на мобильном приложении; список gps координат курьера
        :param params: словарь с ключом и значением  {"request_timeout":"00%3A02%3A00"}
        :return: SyncResultDto Список актуальных доставок для данного курьера
        :rtype:obj:`json`
        """
        # /api/0/mobile/sync?access_token={accessToken}&request_timeout={requestTimeout}&organization={organizationId}
        if send_update_dto is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.sysc.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"send_update_dto\"")
        if params is None:
            params = {"organization": self.org}
        else:
            params += {"organization": self.org}

        self.check_token_time()
        params += {"organization": self.org}
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/mobile/sync?access_token={self.token}',
                params=params,
                data=send_update_dto
            )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.sysc.__name__,
                f"[ERROR] Не удалось сделать запрос полной синхронизации мобильного"
                f"приложения и сервера доставок.\n{err}"
            )


class DeliverySettings(Auth):
    """
    Настройки доставки
    """

    def delivery_discounts(self) -> json:
        """
        Получить список скидок, доступных для применения в доставке для заданного ресторана

        :return:DiscountCardTypeInfo[] Список скидок, доступных для применения в доставочных заказах.
        """
        # /api/0/deliverySettings/deliveryDiscounts?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/deliverySettings/deliveryDiscounts?access_token={self.token}'
                f'&organization={self.org}', )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.delivery_discounts.__name__,
                f"[ERROR] Не удалось получить список скидок, доступных для применения в "
                f"доставке для заданного ресторана.\n{err}"
            )

    def get_delivery_terminals(self) -> json:
        """
        Вернуть список доставочных ресторанов, подключённых к данному ресторану

        :return:DeliveryTerminal[] Список доставочных ресторанов, подключённых к данному ресторану
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryTerminals?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/deliverySettings/getDeliveryTerminals?access_token={self.token}'
                f'&organization={self.org}', )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_delivery_terminals.__name__,
                f"[ERROR] Не удалось получить список доставочных ресторанов, подключённых к данному ресторану\n{err}"
            )

    def get_delivery_restrictions(self) -> json:
        """
        Вернуть список ограничений работы ресторана/сети ресторанов

        :return:DeliveryRestrictions Ограничения работы и список зон доставки
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryRestrictions?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/deliverySettings/getDeliveryRestrictions?access_token={self.token}'
                f'&organization={self.org}', )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_delivery_restrictions.__name__,
                f"[ERROR] Не удалось получить список доставочных ресторанов, подключённых к данному ресторану\n{err}"
            )

    def get_survey_items(self, params: dict = None) -> json.JSONDecoder:
        """
        Вернуть вопросы для отзыва клиента о сделанной доставке

        :param params: {"orderId" : "Идентификатор заказа"}
        :return:SurveyItem[] Список вопросов для отзыва клиента о сделанной доставке
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getSurveyItems?access_token={accessToken}&organization={organizationId}&orderId={orderId}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_survey_items.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/deliverySettings/getSurveyItems?access_token={self.token}'
                f'&organization={self.org}',
                params=params, )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_survey_items.__name__,
                f"[ERROR] Не удалось получить вопросы для отзыва клиента о сделанной доставке\n{err}"
            )

    def get_delivery_courier_mobile_settings(self):
        """
        Вернуть настройки для мобильного приложения курьерской доставки для данного ресторана

        :return:DeliveryCourierMobileSettingsResponse Настройки для мобильного приложения курьерской доставки для
        данного ресторана
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryCourierMobileSettings?access_token={accessToken}&organization={organizationId}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/deliverySettings/getDeliveryCourierMobileSettings?access_token={self.token}'
                f'&organization={self.org}', )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.get_delivery_courier_mobile_settings.__name__,
                f"[ERROR] Не удалось получить настройки для мобильного приложения "
                f"курьерской доставки для данного ресторана\n{err}"
            )


class Olaps(Auth):
    """
    Олапы
    Все методы этого сервиса работают по протоколу https.
    """

    def olap_columns(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить информацию о колонках олап-отчета
        :param params: {"request_timeout" : "00%3A02%3A00", "reportType":"Идентификатор заказа"}
            параметр request_timeout не обязателен,
            тип олап отчёта(reportType) один из : (Sales, Transactions, Deliveries)
        :return: OlapReportColumnsResponse Информация по колонкам олапа заданного типа
        :rtype:obj:`json`
        """
        # /api/0/olaps/olapColumns?access_token={accessToken}&request_timeout={requestTimeout}&organizationId={organizationId}&reportType={reportType}
        if params is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.olap_columns.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"params\"")
        params += {"organization": self.org}
        self.check_token_time()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/olaps/olapColumns?access_token={self.token}', params=params,)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise GetException(
                self.__class__.__qualname__,
                self.olap_columns.__name__,
                f"[ERROR] Не удалось получить информацию о колонках олап-отчета\n{err}"
            )

    def olap(self, olap_report_request: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Получить олап-отчет
        Получить данные олап отчета

        :param olap_report_request: Запрос на получение олап-отчета(POST-параметр. передается в body)
        :param params: {"request_timeout" : "00%3A02%3A00",} не обязателен
        :type params:obj:`dict`
        :return: OlapReportResponse Данные олап-отчета
        """
        # /api/0/olaps/olap?access_token={accessToken}&request_timeout={requestTimeout}
        if olap_report_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.olap.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"olap_report_request\"")
        params += {"organization": self.org}
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/olaps/olap?access_token={self.token}',
                params=params,
                data=olap_report_request, )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.olap.__name__,
                f"[ERROR] Не удалось получить данные олап отчета\n{err}"
            )

    def olap_presets(self, params: dict = None) -> json.JSONDecoder:
        """
        Получить виды преднастроенных олап-отчетов
        :param params: {"request_timeout" : "00%3A02%3A00",} не обязателен
        :return: OlapReportPresetsResponse Информация по видам преднастроенных олап-отчетов для заданной организации.
        """
        # /api/0/olaps/olapPresets?access_token={accessToken}&request_timeout={requestTimeout}&organizationId={organizationId}
        if params is None:
            params = {"organization": self.org}
        else:
            params += {"organization": self.org}

        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/olaps/olapPresets?access_token={self.token}',
                params=params, )
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.olap_presets.__name__,
                f"[ERROR] Не удалось получить виды преднастроенных олап-отчетов\n{err}"
            )

    def olap_by_preset(self, preset_olap_report_request: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Получить преднастроенный олап-отчет

        :param preset_olap_report_request: PresetOlapReportRequest запрос на получение олап-отчета
            (POST-параметр. передается в body)
        :param params:  {"request_timeout" : "00%3A02%3A00",} не обязателен
        :return: OlapReportResponse Данные преднастроенного олап-отчета
        """
        # /api/0/olaps/olapByPreset?access_token={accessToken}&organizationId={organizationId}&request_timeout={requestTimeout}
        if preset_olap_report_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.olap.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"preset_olap_report_request\"")

        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/olaps/olapByPreset?access_token={self.token}&organizationId={self.org}',
                params=params, data=preset_olap_report_request)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.olap_by_preset.__name__,
                f"[ERROR] Не удалось получить преднастроенный олап-отчет\n{err}"
            )


class Events(Auth):
    """
    Журнал событий
    Все методы этого сервиса работают по протоколу https.
    """

    def events(self, events_request: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Получить данные журнала событий

        :param events_request: Запрос на получение журнала событий (POST-параметр. передается в body)
        :param params: {"request_timeout" : "00%3A02%3A00",} не обязательно
        :return: eventsResponse Данные журнала событий
        """
        # /api/0/events/events?access_token={accessToken}&request_timeout={requestTimeout}
        if events_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.events.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"events_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/events/events?access_token={self.token}',
                params=params, data=events_request)
            return result.json()

        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.events.__name__,
                f"[ERROR] Не удалось получить преднастроенный олап-отчет\n{err}"
            )

    def get_events_metadata(self, events_request: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Получить мета данные журнала событий

        :param events_request:запрос на получение мета данных журнала событий (POST-параметр. передается в body)
        :param params: {"request_timeout" : "00%3A02%3A00",} не обязательно
        :return:EventsResponse Данные журнала событий
        """
        # /api/0/events/eventsMetadata?access_token={accessToken}&request_timeout={requestTimeout}
        if events_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.get_events_metadata.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"events_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/events/eventsMetadata?access_token={self.token}',
                params=params, data=events_request, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.get_events_metadata.__name__,
                f"[ERROR] Не удалось получить мета данные журнала событий\n{err}"
            )

    def sessions(self, events_request: dict = None, params: dict = None) -> json.JSONDecoder:
        """
        Получить информацию о кассовых сменах
        Получить информацию о кассовых сменах за операционный период (день)

        :param events_request: запрос на получение мета данных журнала событий (POST-параметр. передается в body)
        :param params: {"request_timeout" : "00%3A02%3A00",} не обязательно
        :return: EventsResponse Данные журнала событий
        """
        # /api/0/events/sessions?access_token={accessToken}&request_timeout={requestTimeout}
        if events_request is None:
            raise ParamSetException(self.__class__.__qualname__,
                                    self.events.__name__,
                                    f"[ERROR] Не присвоен обязательный параметр: \"events_request\"")
        self.check_token_time()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/events/sessions?access_token={self.token}',
                params=params, data=events_request, )
            return result.json()
        except requests.exceptions.RequestException as err:
            raise PostException(
                self.__class__.__qualname__,
                self.sessions.__name__,
                f"[ERROR] Не удалось получить мета данные журнала событий\n{err}"
            )


class BizService(Orders, Nomenclature, Cities,
                 Notices, RMSSettings, StopLists, Mobile,
                 DeliverySettings, Olaps, Events):
    pass
