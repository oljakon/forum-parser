import requests
from bs4 import BeautifulSoup
import re
from hashlib import sha256
import base64
from typing import Optional

website = WEBSITE_URL

class Hasher():
    def __init__(self, topics_hashes: list, msg_hashes: list, users_hashes: list):
        # Массивы с сохраненными хэшами
        self.topics_hashes = topics_hashes
        self.msg_hashes = msg_hashes
        self.users_hashes = users_hashes

    def hash_topic(self, topic: dict) -> bytes:
        h = sha256()
        h.update(topic['topic_name'].encode('utf-8'))
        h.update(topic['replies_number'].encode('utf-8'))
        h.update(topic['last_msg_datetime'].encode('utf-8'))

        return h.digest()

    def hash_msg(self, msg: dict) -> bytes:
        h = sha256()
        h.update(msg['msg_text'].encode('utf-8'))
        h.update(msg['msg_datetime'].encode('utf-8'))
        h.update(msg['msg_author_name'].encode('utf-8'))
        h.update(msg['msg_url'].encode('utf-8'))

        return h.digest()

    def hash_user(self, msg: dict) -> bytes:
        h = sha256()
        h.update(msg['user_name'].encode('utf-8'))
        h.update(msg['user_msg_count'].encode('utf-8'))

        return h.digest()

    # Хэши двух одинаковых записей совпадают
    # Если хэш отсутствует в массиве хэшей, значит, запись новая
    def is_hash_new(self, hash: bytes, hash_array: list) -> bool:
        if hash in hash_array:
            return False
        return True


class ForumParser:
    def __init__(self, parsed_topics_list: list[dict], parsed_messages_list: list[dict], parsed_users_list: list[dict]):
        # Массивы словарей с полученными данными
        self.parsed_topics_list = parsed_topics_list
        self.parsed_messages_list = parsed_messages_list
        self.parsed_users_list = parsed_users_list

    def get_tor_session(self) -> requests.Session:
        session = requests.session()
        # Подключение через tor на 9050 порту
        session.proxies = {'http': 'socks5h://127.0.0.1:9050',
                           'https': 'socks5h://127.0.0.1:9050'}
        return session

    def get_last_page_number(self, response: str) -> Optional[str]:
        soup = BeautifulSoup(response, 'lxml')
        try:
            last_page = soup.find(class_='pageNavSimple-el pageNavSimple-el--last').get('href')
        except AttributeError:
            last_page = None

        return last_page

    def get_all_pages(self, url: str, last_page: str) -> list:
        last_page_number = int(re.search(r'page-(.+)', last_page).group(1))
        urls = []

        for page in range(2, last_page_number + 1):
            urls.append(url + 'page-' + str(page))

        return urls

    def parse_topics(self, response: str) -> list[dict]:
        soup = BeautifulSoup(response, 'lxml')

        topics_main = soup.find_all(class_='structItem-cell structItem-cell--main')
        topics_meta = soup.find_all(class_='structItem-cell structItem-cell--meta')
        topics_latest = soup.find_all(class_='structItem-cell structItem-cell--latest')

        topics = zip(topics_main, topics_meta, topics_latest)

        topics_data = []
        for topic in topics:
            topic_name = str(topic[0].find('a').string)
            topic_url = 'https://mipped.com' + topic[0].find('a').get('href')
            last_msg_datetime = re.search(r'datetime=\"(.+?)\"', str(topic[2].find('a'))).group(1)
            replies_number = str(topic[1].find('dd').string)
            if 'K' in replies_number:
                replies_number = replies_number[:-1] + '000'

            topic_data = {
                'topic_name': topic_name,
                'topic_url': topic_url,
                'last_msg_datetime': last_msg_datetime,
                'replies_number': replies_number
            }

            topics_data.append(topic_data)

        return topics_data

    def parse_messages(self, topic_url: str, topic_response: str) -> list[dict]:
        soup = BeautifulSoup(topic_response, 'lxml')

        messages = soup.find_all(class_='message-cell message-cell--main')
        users_details = soup.find_all(class_='message-userDetails')

        msg_with_users = zip(messages, users_details)

        msgs_data = []
        for message in msg_with_users:
            msg_text = message[0].find(class_='bbWrapper').text
            msg_datetime = re.search(r'datetime=\"(.+?)\"', str(message[0].find('time'))).group(1)
            msg_author_name = re.search(r'itemprop=\"name\">(.+?)<', str(message[1].find('h4').find('a'))).group(1)
            msg_url = topic_url + '#' + message[0].find('a').get('href')

            msg_data = {
                'msg_text': msg_text,
                'msg_datetime': msg_datetime,
                'msg_author_name': msg_author_name,
                'msg_url': msg_url
            }

            msgs_data.append(msg_data)

        return msgs_data

    def parse_users(self, topic_response: str) -> list[dict]:
        soup = BeautifulSoup(topic_response, 'lxml')

        users_details = soup.find_all(class_='message-userDetails')
        users_extra = soup.find_all(class_='message-userExtras')
        user_avatar_jpg = soup.find_all(class_='message-avatar-wrapper')

        users = zip(users_details, users_extra, user_avatar_jpg)

        users_data = []
        for user in users:
            user_name = re.search(r'itemprop=\"name\">(.+?)<', str(user[0].find('h4').find('a'))).group(1)
            if user_name in [item['user_name'] for item in users_data]:
                continue
            user_reputation = re.search(r'<dt>Реакции</dt>\n<dd>(.+?)</dd', str(user[1])).group(1)
            user_msg_count = re.search(r'<dt>Сообщения</dt>\n<dd>(.+?)</dd', str(user[1])).group(1)
            try:
                img = user[2].find('img')
                user_avatar = img.get('data-pagespeed-lazy-src') or img.get('src')
                if user_avatar:
                    user_avatar_url = 'https://mipped.com' + str(user_avatar)
                    user_avatar = base64.b64encode(requests.get(user_avatar_url).content)
            except AttributeError:
                user_avatar = None

            user_data = {
                'user_name': user_name,
                'user_reputation': user_reputation,
                'user_msg_count': user_msg_count,
                'user_avatar': user_avatar
            }

            users_data.append(user_data)

        return users_data


def main():
    parser = ForumParser(parsed_topics_list=[], parsed_messages_list=[], parsed_users_list=[])
    url = website
    session = parser.get_tor_session()
    response = session.get(url)
    response_text = response.text
    response_url = response.url

    hasher = Hasher(topics_hashes=[], msg_hashes=[], users_hashes=[])

    parsed_topics = parser.parse_topics(response_text)
    topics_last_page = parser.get_last_page_number(response_text)

    if topics_last_page:
        all_topics_pages = parser.get_all_pages(response_url, topics_last_page)
        for topics_page_url in all_topics_pages:
            parsed_topics.extend(parser.parse_topics(session.get(topics_page_url).text))
            for topic in parsed_topics:
                topic_hash = hasher.hash_topic(topic)
                if hasher.is_hash_new(topic_hash, hasher.topics_hashes):
                    parser.parsed_topics_list.append(topic)
                    hasher.topics_hashes.append(topic_hash)

    for topic in parser.parsed_topics_list:
        topic_response = session.get(topic['topic_url']).text
        msg_last_page = parser.get_last_page_number(topic_response)

        parsed_messages = parser.parse_messages(topic['topic_url'], topic_response)
        parsed_users = parser.parse_users(topic_response)

        if msg_last_page:
            all_msg_pages = parser.get_all_pages(topic['topic_url'], msg_last_page)
            for msg_page_url in all_msg_pages:
                parsed_messages.extend(parser.parse_messages(msg_page_url, session.get(msg_page_url).text))
                for message in parsed_messages:
                    msg_hash = hasher.hash_msg(message)
                    if hasher.is_hash_new(msg_hash, hasher.msg_hashes):
                        parser.parsed_messages_list.append(message)
                        hasher.msg_hashes.append(msg_hash)

                parsed_users.extend(parser.parse_users(topic_response))
                for user in parsed_users:
                    user_hash = hasher.hash_user(user)
                    if hasher.is_hash_new(user_hash, hasher.msg_hashes):
                        parser.parsed_users_list.append(user)
                        hasher.users_hashes.append(user_hash)


if __name__ == '__main__':
    main()
