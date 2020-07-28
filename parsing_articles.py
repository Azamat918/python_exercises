import requests
import csv
import logging
from bs4 import BeautifulSoup
from time import sleep

ATTEMPTS = 4
SLEEP_SEC = 4
MAIN_LINK = "https://vk.com"
YVKURSE_LINK = "https://vk.com/@yvkurse"
LOAD_MORE_LINK = "https://vk.com/al_articles.php"
CSV_FILE_DIRECTORY = 'parsing_result.csv'
LOGGING_FILE_DIRECTORY = 'parsing_articles.log'


def get_html(url, method='GET', headers=None, data=None, res_type='html'):
    if data is None:
        data = {}
    if headers is None:
        headers = {}
    for i in range(ATTEMPTS):
        try:
            if method == 'POST':
                req = requests.post(url, data=data, headers=headers)
                if res_type == 'json':
                    return req.json()
            else:
                req = requests.get(url)
            return req.text
        except Exception as e:
            logging.error(e)
            logging.info("I am sleeping for 4 sec")
            sleep(SLEEP_SEC)


def get_article_links():
    urls = []
    offset = 30
    headers = {
        'authority': 'vk.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': '*/*',
        'origin': 'https://vk.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://vk.com/^@yvkurse',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': "remixscreen_depth=24; tmr_lvid=d49c52184f0d7500227e8e4a29e38621; "
                  "tmr_lvidTS=1576690516601; remixstid=1552952741_bm2JOQMGsRL6NRPARJjP3KhncI7NYBzuNI2X8XpDlWw; "
                  "remixscreen_width=1536; remixscreen_height=864; remixscreen_dpr=1.25; remixlang=0; "
                  "remixusid=NTFhNzEyYTdhMTdjOTM0ODIxMzA3MjA4; remixflash=0.0.0; remixab=1; "
                  "remixscreen_orient=1; remixua=-1%7C-1%7C174%7C1746444182; remixseenads=0; "
                  "remixrefkey=b6dfe967838768fed1; "
                  "remixsid=37245ef0e49f394c658a2a07aa72bdb5d6c124707e220303c2976a19c0f80; "
                  "remixgp=7365d6dbb84c021f98ef81350a596c22; remixdt=-10800; remixscreen_winzoom=1.52; "
                  "tmr_detect=1%7C1595938289060; tmr_reqNum=290",
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
        res_json = get_html(LOAD_MORE_LINK, 'POST', headers=headers, data=data, res_type='json')
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
                continue
            except Exception as e:
                logging.warning(e)
                return None
        page_grid_titles = soup.find_all('div', class_='author_page_grid_article')
        if page_grid_titles is None or len(page_grid_titles) == 0:
            break
        else:
            if len(page_grid_titles) > 0:
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


def get_text_img_article(url, article_title):
    try:
        soup = BeautifulSoup(get_html(url), 'lxml')
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

def parse_yvkurse_link():
    urls = []
    try:
        html = get_html(YVKURSE_LINK)
        soup = BeautifulSoup(html, 'lxml')
        author_page_articles = soup.find_all('div', class_='author-page-article')
        if len(author_page_articles) > 0:
            for author_page_article in author_page_articles:
                name = author_page_article.find('span', class_='author-page-article__title').text
                url = MAIN_LINK + author_page_article.a['href']
                urls.append({'name': name, 'url': url})
        else:
            return None
    except Exception as e:
        logging.error(e)
        return None

    return urls

def main():
    urls = get_article_links()
    if urls is None:
        logging.info("LOAD_MORE link return None, try parse YVKURSE_LINK")
        urls = parse_yvkurse_link()
    if urls is not None:
        logging.info('TOTAL Articles: {}'.format(str(len(urls))))
        if write_headers_of_file():
            for url in urls:
                logging.info("PARSING: {} {}".format(url['url'], url['name']))
                res = get_text_img_article(url['url'], url['name'])
                if res is False:
                    break
    else:
        print("Something wrong. LOAD_MORE and YVKURSE LINKS returned NONE")


if __name__ == "__main__":
    logging.basicConfig(handlers=[logging.FileHandler(LOGGING_FILE_DIRECTORY, 'a', 'utf-8')], level=logging.INFO)
    main()
