# parsing articles
parsing_articles.py - скрипт который парсит статьи из группы https://vk.com/@yvkurse и записывает в CSV файл.

версия python: Python 3.7.8
версия pip: pip 20.1.1

Запуск:
- 1.Перед запуском необходимо установить все зависимости и доп. библиотеки - "pip install -r requirements.txt"
- 2.При запуске надо указать логин и пароль от вк для того чтобы бот смог парсить все данные и статьи.
- 3.Запускаем файл parsing_articles.py - "python parsing_articles.py 87124567845 password", парсит: "Загаловок, Параграфы, Фото, Ссылку"

CSV файл:
- Название файла: parsing_result.csv
- Разделителем является '|'
- закодирован в UTF-8

Логирование:
- Название файла: parsing_articles.log

