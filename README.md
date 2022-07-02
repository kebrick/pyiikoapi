# pyiikoapi

# Сообщение от компании IIKO!!!
# Внимание! С 1 июля 2022 года мы прекратим предоставлять API iiko.biz для создания новых интеграций с iiko. Все будущие интеграции с внешними системами доставки будут создаваться на базе iiko Cloud API. При этом до конца 2022 года мы будем продолжать поддержку уже реализованных интеграционных решений в рамках существующих лицензионных контрактов.


## Python services for convenient work with iiko Biz API and iiko Card API

### Requirements
- Python 3.5 or higher.

### Install
    pip install pyiikoapi
## Read more [Biz](biz/readme.md) readme
### Example
    from pyiikoapi import BizService or from pyiikoapi.biz import BizService

    # class initialization
    api = BizService(login,password,organizationId)
    
    # receive a list of the organization's couriers
    couriers = api.get_couriers()
## Read more [Card](card/readme.md) readme
### Example
    from pyiikoapi import CardService or from pyiikoapi.card import CardService
    
    # class initialization 
    api = CardService(login,password,organizationId)
    
    # get a list of organizations, i define request_timeout = 2 minutes
    organization_info = api.list(params={"request_timeout": "00%3A02%3A00"})

### Инфо
Маркер доступа автоматически запрашивается при инициализации классов, а так же при каждом вызове любого из методов он будет проверять время жизни маркера доступа, если время жизни маркера прошло то будет автоматически запрошен заново.

**Время жизни маркера доступа равно 15 минутам.**

**_"organizationId" прописывайте при инициализации класса_**
