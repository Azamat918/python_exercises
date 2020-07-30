import requests
import csv
import logging
import sys
from bs4 import BeautifulSoup
from time import sleep
import lxml.html

ATTEMPTS = 4
SLEEP_SEC = 4
LOGIN = None
PASSWORD = None
MAIN_LINK = "https://vk.com"
LOAD_MORE_LINK = "https://vk.com/al_articles.php"
CSV_FILE_DIRECTORY = 'parsing_result.csv'
LOGGING_FILE_DIRECTORY = 'parsing_articles.log'


def get_html(session, url, method='GET', headers=None, data=None, res_type='html'):
    if data is None:
        data = {}
    if headers is None:
        headers = {}
    for i in range(ATTEMPTS):
        try:
            if method == 'POST':
                req = session.post(url, data=data, headers=headers, timeout=10)
                if res_type == 'json':
                    return req.json()
            else:
                req = session.get(url, timeout=10)
            return req.text
        except Exception as e:
            logging.error(e)
            logging.info("I am sleeping for 4 sec")
            sleep(SLEEP_SEC)


def get_article_links(session):
    urls = []
    offset = 30
    headers = {
        'authority': 'vk.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/61.0.3163.100 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': '*/*',
        'origin': 'https://vk.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://vk.com/^@yvkurse',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    data = {
        'act': 'author_page_more',
        'al': '1',
        'articles_offset': '0',
        'need_drafts': '0',
        'owner_id': '-73519170',
        'sort_by': 'date'
    }
    while True:
        res_json = get_html(session, LOAD_MORE_LINK, 'POST', headers=headers, data=data, res_type='json')
        try:
            soup = BeautifulSoup(res_json['payload'][1][0][0], 'lxml')
        except Exception as e:
            logging.error(e)
            return None
        if data['articles_offset'] == '0':
            try:
                name_url = {'url': MAIN_LINK + soup.a['href'],
                            'name': soup.find('div', class_='author_page_article_title').text}
                data['articles_offset'] = '1'
                urls.append(name_url)
            except Exception as e:
                logging.warning(e)
                return None
        else:
            page_grid_titles = soup.find_all('div', class_='author_page_grid_article')
            if page_grid_titles is None or len(page_grid_titles) == 0:
                break
            else:
                for page_grid_title in page_grid_titles:
                    try:
                        title = page_grid_title.a.find('div', class_='author_page_article_title')
                        name_url = {'url': MAIN_LINK + page_grid_title.a['href'],
                                    'name': title.text}
                        urls.append(name_url)
                    except Exception as e:
                        logging.warning(e)
                        return None
            data['articles_offset'] = int(data['articles_offset']) + offset

    return urls


def login_vk(session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    data = session.get(MAIN_LINK, headers=headers)
    page = lxml.html.fromstring(data.content)
    form = page.forms[0]
    form.fields['email'] = LOGIN
    form.fields['pass'] = PASSWORD
    response = session.post(form.action, data=form.form_values())
    if 'onLoginDone' in response.text:
        return session
    else:
        return None


def get_text_img_article(session, url, article_title):
    try:
        soup = BeautifulSoup(get_html(session, url), 'lxml')
        article_view = soup.find('div', class_='article_view')
        paragraphs = article_view.find_all('p')
        imgs = article_view.find_all('img')

        paragraphs = '\n'.join([p.text for p in paragraphs])
        imgs = '\n'.join([img['src'] for img in imgs])
    except Exception as e:
        logging.error(e)
        return False

    write_to_csv_file(imgs, paragraphs, article_title, url)
    return True


def write_to_csv_file(imgs, paragraphs, article_title, url):
    logging.info("WRITING: {} {}".format(str(url), str(article_title)))
    try:
        with open(CSV_FILE_DIRECTORY, 'a', encoding='utf-8') as file:
            csv_writer = csv.DictWriter(file, fieldnames=['Title', 'Paragraphs', 'Images', 'Url'], delimiter='|')
            csv_writer.writerow({
                'Title': article_title,
                'Paragraphs': paragraphs,
                'Images': imgs,
                'Url': url
            })
    except Exception as e:
        logging.error(e)


def write_headers_of_file():
    try:
        with open(CSV_FILE_DIRECTORY, 'a', encoding='utf-8') as file:
            csv_writer = csv.DictWriter(file, fieldnames=['Title', 'Paragraphs', 'Images', 'Url'], delimiter='|')
            csv_writer.writeheader()
        return True
    except Exception as e:
        logging.error(e)
        return False


def main():
    global LOGIN, PASSWORD
    if len(sys.argv) >= 3:
        try:
            LOGIN = sys.argv[1]
            PASSWORD = sys.argv[2]
        except Exception as e:
            logging.error(e)
    if LOGIN is not None and PASSWORD is not None:
        session = requests.session()
        session = login_vk(session)
        if session is not None:
            urls = get_article_links(session)
            if urls is not None:
                logging.info('TOTAL Articles: {}'.format(str(len(urls))))
                if write_headers_of_file():
                    for url in urls:
                        logging.info("PARSING: {} {}".format(url['url'], url['name']))
                        res = get_text_img_article(session, url['url'], url['name'])
                        if res is False:
                            break
            else:
                logging.info('Couldnt get urls of articles, urls is None')
        else:
            logging.info('Login Failed, login:{} password{}'.format(LOGIN, PASSWORD))
            print('Login Failed Please write another login and password')
    else:
        print('Please write login and password')


if __name__ == "__main__":
    logging.basicConfig(handlers=[logging.FileHandler(LOGGING_FILE_DIRECTORY, 'a', 'utf-8')], level=logging.INFO)
    main()
