# django_knowledge

"django knowledge" - это сервер базы знаний. Призван обеспечить:
- выгрузку данных из резервного хранилища в рабочее и наоборот;
- полнотекстовый поиск по хранилищу;
- добавления
- удобные API- и GUI-инструменты для управления выгрузкой, наполнения и поиска даных из различных внешних систем. Например, чат боты, приложения для веб и смартфонов.

# Интеграция с сервисами хранения и поиска информации

## Настройка Typesense

Команды для закгрузки, установки и запуска сервера Typesense: 
```sh
wget https://dl.typesense.org/releases/0.22.1/typesense-server-0.22.1-linux-amd64.tar.gz
tar -xf typesense-server-0.22.1-linux-amd64.tar.gz
mkdir data
./typesense-server --data-dir=data --api-key=your_any_key &> /dev/null &
curl http://localhost:8108/health
```

Ключи запуска сервера:
- `--data-dir` - директория, в которой Typesense будет хранит базу данных. В примере это `data`;
- `--api-key` - ключ, по которому осуществляется досту к Typesense. В примере это `your_any_key`.

- Подробное описание установки: https://typesense.org/docs/guide/install-typesense.html#%F0%9F%8E%AC-start
- Описание API для работы с документами Typesense (включая разные способы поиска): https://typesense.org/docs/0.22.1/api/documents.html#federated-multi-search
- Примеры использования: https://github.com/typesense/typesense-python/blob/master/examples
 
## Firebase

Данная облачная база не поддерживает полнотекстовый поиск, а только поиск по точному совпадению значения. Для интеграции с полнотекстовыми системами на странице документации [предлагаются платные плагины](https://firebase.google.com/docs/firestore/solutions/search).

# Планируемое универсальное API сервера

## База знаний

Поиск статьи
- метод: `GET note/search`
- аргументы:
    - `title` - фраза для поиска по заголовку статьи,
    - `content` - фраза для поиска по содержимому статьи,
    - `source` - наименование базы, по которой произойдёт поиск; необязательный аргумент

Добавить статью
- метод: `POST note/add`
- аргументы:
    - `title` - заголовок статьи
    - `content` - содержимое статьи
    - `source` - наименование базы, в которую добавится статья; необязательный аргумент

Получить статью
- метод: `GET note/get`
- аргументы:
    - `title` - заголовок статьи
    - `source` - наименование базы, из которой будет получена статья; необязательный аргумент

## База книг

Поиск книг:
- метод: `GET book/search`
- аргументы:
    - `title` - фраза для поиска по названию книги,
    - `tag` - фраза для поиска по тегу, с которой сопоставлена книга,
    - `source` - наименование базы, по которой произойдёт поиск; необязательный аргумент

## База навыков

Раздел не написан.