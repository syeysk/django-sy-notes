# Платформа межкомандного взаимодействия

## Введение

Проект воплощает идею творческого пространства как набора отдельных, простых, но взаимосвязанных функций, подключаемых по мере необходимости.

Данный репозиторий – это веб-интерфейс, собирающий микросервисы в единое пространство.

### Предыстория

Сервис является форком сервиса tvp-support/knowledge-api, который реализовался как спешный и экспериментальный вариант приложения tvp-support/activista.

### Веб интерфейс

Пространство (space) состоит из площадей (square). На площади организованы комнаты-приложения (apps)

У всех людей общее пространство, каждый человек может иметь площади под разные потребности (разные бизнесы, НКО, например)

## Запуск

Скачивание репозитория:

```sh
git clone https://github.com/TVP-Support/django_knowledge
```

Установка зависимостей:

```sh
pip install -r requirements.txt
```

Применение миграций:

```sh
python manage.py migrate
```

Заполнить переменные окружения, добавив и заполнив файл `.env`

Запуск сервера:

```sh
python manage.py runserver
```

Проверка доступности сервера:

<http://127.0.0.1:8000/api/v1/note/search/query/>

HTTP/2 200 возвращает JSON ответ.

## API сервера

[Документация API](https://github.com/TVP-Support/django_knowledge/wiki)

## План разработки сервиса и микросервисов

1. [Трансформация форка](ROADMAP_001_transformation_of_fork.md)
2. [Улучшение сервиса и добавление новых модулей](ROADMAP_002_improvements_and_new_modules.md)
3. [Интеграция сервиса с внешними сервисами](ROADMAP_003_integration_with_external_services.md)

## Вдохновение

Источником вдохновения стали программы:

- Blender - идентичные комбинации клавиш и названия команд в разных рабочих пространствах, переиспользование созданного в одном пространстве объекта в другом пространстве;
- FreeCAD - взгляд на CAD-систему как на набор отдельных кардинально различающихся по функциям и назначению верстаков, переиспользование созданного в одном пространстве объекта в другом пространстве;
- [activista](https://github.com/TVP-Support/activista) - идея объединить разнообразные по назначению микросервисы для реализации пользовательских проектов.
