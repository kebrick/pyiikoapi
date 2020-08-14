import requests
import json

class IikoBizAPI:
    def __init__(self, login, password, org):

        self.login = login
        self.password = password
        self.org = org

        try:
            self.token = requests.get(
                f'https://iiko.biz:9900/api/0/auth/access_token?user_id={self.login}&user_secret={self.password}',
                timeout=5).text[1:-1]

        except requests.exceptions.ConnectTimeout:
            print("\n\nНе удалось получить токен " + "\n" + self.login)


    def __str__(self):
        return self.token
    def organization(self):
        """Организации"""
        try:

            return list(requests.get(f'https://iiko.biz:9900/api/0/organization/list?access_token={self.token}').json())
        except requests.exceptions.ConnectTimeout:
            print(
                "\n\nНе удалось получить список организаций " + "\n" + self.login)

    def couriers(self):
        """Все курьеры"""
        try:
            return list(requests.get(
                f'https://iiko.biz:9900/api/0/rmsSettings/getCouriers?access_token={self.token}&organization={self.org}').json()[
                            'users'])

        except requests.exceptions.ConnectTimeout:
            print("\n\nНе удалось получить курьеров " + "\n" + self.login)

    def orders_courier(self, courier) -> list:
        """Активные заказы курьера"""
        try:
            return list(requests.get(
                f'https://iiko.biz:9900/api/0/orders/get_courier_orders?access_token={self.token}&organization={self.org}&courier={courier}&request_timeout=00%3A02%3A00').json()[
                            'deliveryOrders'])

        except requests.exceptions.ConnectTimeout:
            print("Не удалось получить заказы " + "\n" + self.login)

    def all_orders(self, **kwargs):
        """Все заказы"""
        try:
            return list(requests.get(
                f'https://iiko.biz:9900/api/0/orders/deliveryOrders?access_token={self.token}',
                params=kwargs).json())

        except requests.exceptions.ConnectTimeout:
            print("Не получить заказы " + "\n" + self.login)

    def set_order_delivered(self, SetOrderDeliveredRequest):
        """Отправить подтверждеие """

        try:
            return requests.post(
                f'https://iiko.biz:9900/api/0/orders/set_order_delivered?access_token={self.token}&organization={self.org}&request_timeout=00%3A02%3A00',
                data=SetOrderDeliveredRequest)
        #data=SetOrderDeliveredRequest
        #json = json.dumps(SetOrderDeliveredRequest)

        except requests.exceptions.ConnectTimeout:
            print("Подтверждение не отправлено! ")


