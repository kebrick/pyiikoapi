import requests
from datetime import datetime as dt
from datetime import timedelta as td
from .exception import TokenException
from .exception import GetException
from .exception import PostException
from .exception import SetSession
import json


class AuthBiz:
    """
    Если не был присвоен костомный session то по стандарту header будет равняться:
    {
    'Content-type': 'application/json',
    'Accept': 'application/json',
    'Content-Encoding': 'utf-8'
    }
    """

    def __init__(self, login: str, password: str, org: str, session: requests.Session = None):
        self.__session = requests.Session()
        if session is not None:
            self.__session = session

        self.__login = login
        self.__password = password
        self.__org = org
        self.__token = None
        self.__time_token = None
        self.__base_url = "https://iiko.biz:9900"

        # self.request_timeout = "00%3A02%3A00"

    def checkout_time_token(self) -> bool:
        """
        Проверка на время жизни маркера доступа
        :return: Если прошло 15 мин будет запрошен токен и метод вернёт True, иначе вернётся False
        """
        fifteen_minutes_ago = dt.now() - td(minutes=15)
        time_token = self.__time_token
        if time_token <= fifteen_minutes_ago:
            print(f"Update token: {self.get_token()}")
            return True
        else:
            return False

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
                f"[ERROR] Не присвоен обьект типа requests.Session")
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

    def get_token(self) -> str:
        """Получить маркер доступа"""
        try:
            result = self.session_s.get(
                f'{self.__base_url}/api/0/auth/access_token?user_id={self.__login}&user_secret={self.__password}')
            self.__token = result.text[1:-1]
            self.__time_token = dt.now()
            return result.text[1:-1]

        except requests.exceptions.RequestException as err:
            raise TokenException(self.__class__.__qualname__,
                                 self.get_token.__name__,
                                 f"[ERROR] Не удалось получить маркер доступа: \n{err}")


class Orders(AuthBiz):
    """
    Сервис для работы с разделом заказов iiko Biz Api
    Все методы возвращают чистый json
    """

    def get_courier_orders(self, courierId: str, **params: dict) -> json:
        """
        Активные заказы курьера

        :param courierId: id courier
        :type courierId: :obj:`str`
        :param params: {"request_timeout" : "00%3A02%3A00"}
        """

        self.checkout_time_token()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/get_courier_orders?access_token={self.token}'
                f'&organization={self.org}&courier={courierId}',
                # f'&request_timeout=00%3A02%3A00'
                params=params)
            return result.json()  # ['deliveryOrders']

        except requests.exceptions.ConnectTimeout:
            raise GetException(self.__class__.__qualname__,
                               self.get_courier_orders.__name__,
                               f"[ERROR] Не удалось получить активные заказы курьера")

    def delivery_orders(self, **params) -> json:
        """
        Все заказы
        :param params: {"dateFrom": "","dateTo" : "", "deliveryStatus" : "", "deliveryTerminalId" : "", "request_timeout" : "00%3A02%3A00"}

        """
        self.checkout_time_token()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/orders/deliveryOrders?access_token={self.token}&organization={self.org}',
                params=params)
            return result.json()

        except requests.exceptions.ConnectTimeout:
            raise GetException(self.__class__.__qualname__,
                               self.delivery_orders.__name__,
                               f"[ERROR] Не удалось получить активные заказы курьера")

    def set_order_delivered(self, set_order_delivered_request: dict, **params: dict):
        """
        Отправить подтверждеие

        :param set_order_delivered_request:
        :param params: {"request_timeout" : "00%3A02%3A00"}
        :return: http status code
        """
        self.checkout_time_token()
        try:
            result = self.session_s.post(
                f'{self.base_url}/api/0/orders/set_order_delivered?access_token={self.token}&organization='
                f'{self.org}',
                params=params,
                data=set_order_delivered_request, )
            return result.status_code

        except requests.exceptions.RequestException:
            raise PostException(
                self.__class__.__qualname__,
                self.set_order_delivered.__name__,
                f"[ERROR] Не удалось отправить подтверждеие\n"
            )


class Organization(AuthBiz):
    def get_organization(self) -> json:
        """Организации"""
        self.checkout_time_token()
        try:
            result = self.session_s.get(f'{self.base_url}api/0/organization/list?access_token={self.token}')
            return result.json()
        except requests.exceptions.ConnectTimeout:
            raise GetException(
                self.__class__.__qualname__,
                self.get_organization.__name__,
                f"[ERROR] Не удалось получить организации\n"
            )


class Nomenclature(AuthBiz):
    def nomenclature(self) -> json:
        # /api/0/nomenclature/{organizationId}?access_token={accessToken}
        pass


class Cities(AuthBiz):
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
        pass

    def cities_list(self):
        """
        Получение списка городов организации
        Метод возвращает список всех городов заданной организации. Эти данные могут быть
        использовать для задания адреса доставки.

        :return: City[] Города
        """
        # /api/0/cities/citiesList?access_token={accessToken}&organization={organizationId}
        pass

    def streets(self, cityId: str):
        """
        Получение списка улиц города заданной организации
        Метод возвращает список всех городов заданной организации. Эти данные могут быть
        использовать для задания адреса доставки.

        :param cityId: Идентификатор города
        :return: Street[] Улицы
        """
        # /api/0/streets/streets?access_token={accessToken}&organization={organizationId}&city={cityId}
        pass

    def regions(self):
        """
        Получение списка регионов
        Метод возвращает список всех всех регионов, которые есть в справочнике регионов организации.
        Эти данные могут быть использовать для задания региона в адресе доставки.

        :return: Region[] Список регионов
        """
        # /api/0/regions/regions?access_token={accessToken}&organization={organizationId}
        pass


class Notices(AuthBiz):
    """
    Уведомления
    Все методы этого сервиса работают по протоколу https.
    """

    def notices(self, **params) -> json:
        """
        Получить данные журнала событий

        :param params: информация об уведомлениях (POST-параметр. передается в body)
        :return :NoticesResponse :ответ об успешности операции отправки
        :rtype :obj:`json`
        """
        # /api/0/notices/notices?access_token={accessToken}&request_timeout={requestTimeout}
        pass


class RMSSettings(AuthBiz):
    def supported_protocols(self) -> json:
        """
        :return: OrganizationSupportedProtocol[] :Список протоколов, поддерживаемых организацией
        """
        # /api/0/rmsSettings/supportedProtocols?access_token={accessToken}&organization={organizationId}
        pass

    def get_roles(self) -> json:
        """
        :return :OrganizationRole: Список всех ролей организации Response
        """
        # /api/0/rmsSettings/getRoles?access_token={accessToken}&organization={organizationId}
        pass

    def get_employees(self) -> json:
        """
        :return : OrganizationUser: Список всех сотрудников организации Response
        """
        # /api/0/rmsSettings/getEmployees?access_token={accessToken}&organization={organizationId}
        pass

    def get_restaurant_sections(self) -> json:
        """
        :return :RestaurantSectionsResponse :Список всех залов организации
        """
        # /api/0/rmsSettings/getRestaurantSections?access_token={accessToken}&organization={organizationId}
        pass

    def get_orders_types(self) -> json:
        """
        :return :OrderTypesResponse Справочник типов заказов
        """
        # /api/0/rmsSettings/getOrderTypes?access_token={accessToken}&organization={organizationId}
        pass

    def get_payment_types(self) -> json:
        """
        :return PaymentType[] Внешние типы оплат
        """
        # /api/0/rmsSettings/getPaymentTypes?access_token={accessToken}&organization={organizationId}
        pass

    def get_marketing_sources(self):
        """
        :return: MarketingSourceInfo[] Маркетинговые источники
        """
        # /api/0/rmsSettings/getMarketingSources?access_token={accessToken}&organization={organizationId}
        pass

    def get_couriers(self) -> json:
        """
        All couriers.

        :return: deliveryOrders: struct
        :rtype: json: :obj:`json`
        """
        self.checkout_time_token()
        try:
            result = self.session_s.get(
                f'{self.base_url}/api/0/rmsSettings/getCouriers?access_token={self.token}'
                f'&organization={self.org}')
            return result.json()  # ['users']

        except requests.exceptions.ConnectTimeout:
            raise GetException(
                self.__class__.__qualname__,
                self.get_couriers.__name__,
                f"[ERROR] Не удалось получить список курьеров\n"
            )


class StopLists(AuthBiz):
    def get_delivery_stop_list(self):
        """
        Запрос возвращает список продуктов, находящихся в стоп-листе.
        В случае запроса на колл-центра в результате могут находяится позиции стоп-листа из
        других ресторанов.

        :return: StopListAtOrganization[] Элементы стоп-листа; string[] Идентификаторы организаций, которые не зарегистрированы в iikoBiz.
        """
        # /api/0/stopLists/getDeliveryStopList?access_token={accessToken}&organization={organizationId}
        pass


class Mobile(AuthBiz):
    """
    Мобильное приложение курьера
    """

    def signin(self, **params):
        """
        Запрос логина курьера доставки на удаленный РМС сервер

        :param params:  Сущность, описывающая запрос на логин
        :return: MobileLoginResult DTO, описывающий результат логина (есть ли Dto ошибки), сообщает также версию сервера
        :rtype:obj:`json`
        """
        # /api/0/mobile/signin?access_token={accessToken}&request_timeout={requestTimeout}&organization={organizationId}
        pass

    def sysc(self, **params):
        """
        Запрос полной синхронизации мобильного приложения и сервера доставок
        Отсылает изменения в доставках (статус, проблема) и сохраненные gps координаты курьера.

        :param params: Изменения доставок на мобильном приложении; список gps координат курьера
        :return: SyncResultDto Список актуальных доставок для данного курьера
        :rtype:obj:`json`
        """
        # /api/0/mobile/sync?access_token={accessToken}&request_timeout={requestTimeout}&organization={organizationId}
        pass


class DeliverySettings(AuthBiz):
    """
    Настройки доставки
    """

    def delivery_discounts(self):
        """
        Получить список скидок, доступных для применения в доставке для заданного ресторана

        :return:DiscountCardTypeInfo[] Список скидок, доступных для применения в доставочных заказах.
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/deliveryDiscounts?access_token={accessToken}&organization={organizationId}
        pass

    def get_delivery_terminals(self):
        """
        Вернуть список доставочных ресторанов, подключённых к данному ресторану

        :return:DeliveryTerminal[] Список доставочных ресторанов, подключённых к данному ресторану
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryTerminals?access_token={accessToken}&organization={organizationId}
        pass

    def get_delivery_restrictions(self):
        """
        Вернуть список ограничений работы ресторана/сети ресторанов

        :return:DeliveryRestrictions Ограничения работы и список зон доставки
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryRestrictions?access_token={accessToken}&organization={organizationId}
        pass

    def get_survey_items(self):
        """
        Вернуть вопросы для отзыва клиента о сделанной доставке

        :return:SurveyItem[] Список вопросов для отзыва клиента о сделанной доставке
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getSurveyItems?access_token={accessToken}&organization={organizationId}&orderId={orderId}
        pass

    def get_delivery_courier_mobile_settings(self):
        """
        Вернуть настройки для мобильного приложения курьерской доставки для данного ресторана

        :return:DeliveryCourierMobileSettingsResponse Настройки для мобильного приложения курьерской доставки для
        данного ресторана
        :rtype:obj:`json`
        """
        # /api/0/deliverySettings/getDeliveryCourierMobileSettings?access_token={accessToken}&organization={organizationId}
        pass


class Olaps(AuthBiz):
    """
    Олапы
    Все методы этого сервиса работают по протоколу https.
    """

    def olap_columns(self, olap_reports):
        """
        Получить информацию о колонках олап-отчета
        :param olap_reports: тип олап отчёта (Sales, Transactions, Deliveries)
        :return: OlapReportColumnsResponse Информация по колонкам олапа заданного типа
        :rtype:obj:`json`
        """
        # /api/0/olaps/olapColumns?access_token={accessToken}&request_timeout={requestTimeout}&organizationId={organizationId}&reportType={reportType}
        pass

    def olap(self, **params: dict):
        """
        Получить олап-отчет
        Получить данные олап отчета

        :param params: Запрос на получение олап-отчета(POST-параметр. передается в body)
        :type params:obj:`dict`
        :return: OlapReportResponse Данные олап-отчета
        """
        # /api/0/olaps/olap?access_token={accessToken}&request_timeout={requestTimeout}
        pass

    def olap_presets(self):
        """
        Получить виды преднастроенных олап-отчетов
        :return: OlapReportPresetsResponse Информация по видам преднастроенных олап-отчетов для заданной организации.
        """
        # /api/0/olaps/olapPresets?access_token={accessToken}&request_timeout={requestTimeout}&organizationId={organizationId}
        pass

    def olap_by_preset(self, **presetOlapReportRequest: dict) -> json:
        """
        Получить преднастроенный олап-отчет

        :param presetOlapReportRequest: PresetOlapReportRequest запрос на получение олап-отчета(POST-параметр. передается в body)
        :return: OlapReportResponse Данные преднастроенного олап-отчета
        """
        # /api/0/olaps/olapByPreset?access_token={accessToken}&organizationId={organizationId}&request_timeout={requestTimeout}
        pass


class Events(AuthBiz):
    """
    Журнал событий
    Все методы этого сервиса работают по протоколу https.
    """

    def events(self, **eventsRequest: dict) -> json:
        """
        Получить данные журнала событий

        :param eventsRequest: Запрос на получение журнала событий (POST-параметр. передается в body)
        :return: eventsResponse Данные журнала событий
        """
        # /api/0/events/events?access_token={accessToken}&request_timeout={requestTimeout}
        pass

    def get_events_metadata(self, **eventsRequest: dict):
        """
        Получить мета данные журнала событий

        :param eventsRequest:запрос на получение мета данных журнала событий (POST-параметр. передается в body)
        :return:EventsResponse Данные журнала событий
        """
        # /api/0/events/eventsMetadata?access_token={accessToken}&request_timeout={requestTimeout}\
        pass

    def sessions(self, **eventsRequest: json):
        """
        Получить информацию о кассовых сменах
        Получить информацию о кассовых сменах за операционный период (день)

        :param eventsRequest: запрос на получение мета данных журнала событий (POST-параметр. передается в body)
        :return: EventsResponse Данные журнала событий
        """
        # /api/0/events/sessions?access_token={accessToken}&request_timeout={requestTimeout}
        pass


class BizAPI(Orders, Organization, Nomenclature, Cities,
             Notices, RMSSettings, StopLists, Mobile,
             DeliverySettings, Olaps, Events):
    pass
