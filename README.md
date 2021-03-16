# pyiikoapi

### Python services for working with iiko API

Маркер доступа автоматически запрашивается при инициализации классов, а так же при каждом вызове любого из методов он будет проверять время жизни маркера доступа, если время жизни маркера прошло то будет автоматически запрошен заново.
**Время жизни маркера доступа равно 15 минутам.**

**_"organizationId" прописывайте при инициализации класса_**
## Read more [Biz](./biz/readme.md) readme
#### Example
    from biz import BizService

    # инициализация класса 
    api = BizService(login,password,organizationId)
    # получаю список курьеров организации
    couriers = api.get_couriers()
## Read more [Card](./card/readme.md) readme
#### Example
    from card import CardService
    
    # инициализация класса 
    api = CardService(login,password,organizationId)
    # получаю список организаций, определяю request_timeout = 2 минутам
    organization_info = api.list(params={"request_timeout": "00%3A02%3A00"})
