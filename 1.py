"""
1. http://quotes.toscrape.com/ - написати скрейпер для збору всієї доступної інформації про записи:
   цитата, автор, інфа про автора... Отриману інформацію зберегти в CSV файл та в базу. Результати зберегти в репозиторії.
   Пагінацію по сторінкам робити динамічною (знаходите лінку на наступну сторінку і берете з неї URL). Хто захардкодить
   пагінацію зміною номеру сторінки в УРЛі - буде наказаний ;)
"""
import csv
import sqlite3
import requests
from bs4 import BeautifulSoup

FILENAME = "page_data.csv"
authors_info_list: list = []


def get_requests_url(arg_url=""):
    url = 'http://quotes.toscrape.com' + f'{arg_url}'
    return url


def write_to_csv_file(data: list):
    with open(FILENAME, "w", newline="", encoding='utf-8') as file:
        columns = ["Author", "Birthdate", "Birthplace", "Tags", "Quote", "About"]
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)


def csv_import_to_db():
    contents = None
    connection = sqlite3.connect('pae_data.db')
    cursor = connection.cursor()
    create_table = '''CREATE TABLE IF NOT EXISTS quotes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Author TEXT NOT NULL,
                    Birthdate TEXT NOT NULL,
                    Birthplace TEXT NOT NULL,
                    Tags TEXT NOT NULL,
                    Quote TEXT NOT NULL,
                    About TEXT NOT NULL
                    );'''

    cursor.execute(create_table)

    file = open(FILENAME, "r", encoding="utf8")
    contents = csv.reader(file)

    insert_records = "INSERT INTO quotes (Author, Birthdate, Birthplace, Tags, Quote, About) VALUES(?, ?, ?, ?, ?, ?)"
    cursor.executemany(insert_records, contents)
    connection.commit()
    connection.close()


def page_parse(text: str, authors: str, tags: str, link: str):
    for i in range(0, len(text)):
        authors_info: dict = {}
        tags_list: list = []

        print(text[i].text)
        tags_s_first = tags[i].find_all('a', class_='tag')
        for tg in tags_s_first:
            print(f"Tags: {tg.text}")
            tags_list.append(tg.text)
        print(f"Author: {authors[i].text}")
        print(f"{'-' * 47}About{'-' * 47}")
        link_first = link[i].find_next()

        rec_aut = requests.get(get_requests_url(link_first.get("href")))
        soup_aut = BeautifulSoup(rec_aut.text, "lxml")
        about_s = soup_aut.find("div", class_="author-description")
        about_s_dorn = soup_aut.find("span", class_="author-born-date")
        about_s_born_location = soup_aut.find("span", class_="author-born-location")

        print(f"Author: {authors[i].text}\n")
        print(f'Born: {about_s_dorn.text}, {about_s_born_location.text}\n')
        print("Description:\n")
        print(about_s.text.strip())
        print("*" * 100)

        authors_info = {"Author": authors[i].text,
                        "Birthdate": about_s_dorn.text,
                        "Birthplace": about_s_born_location.text,
                        "Tags": tags_list,
                        "Quote": text[i].text,
                        "About": about_s.text.strip()}
        authors_info_list.append(authors_info)


def parser_web():
    page_num: int = 1
    href_tmp: str = None
    link_tmp: str = None

    rec = requests.get(get_requests_url())
    soup = BeautifulSoup(rec.text, "lxml")
    page = soup.find("li", class_="next").find_next()

    while True:
        try:
            href_tmp = page.get("href")
            link_tmp = href_tmp[0: 6]
            link_tmp = link_tmp + str(page_num)
            url_tmp: str = get_requests_url(link_tmp)
            page_num += 1

            rec = requests.get(url_tmp)
            soup = BeautifulSoup(rec.text, "lxml")
            text_s = soup.find_all('span', class_="text")
            authors_s = soup.find_all('small', class_="author")
            tags_s = soup.find_all('div', class_="tags")
            link_all = soup.find_all('small', class_="author")

            page_parse(text_s, authors_s, tags_s, link_all)

            page = soup.find("li", class_="next").find_next()
            print(f'Page #{page.get("href")[6: 7]}')

        except Exception as Err:
            print("No page available")
            write_to_csv_file(authors_info_list)
            csv_import_to_db()
            break


parser_web()


