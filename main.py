import requests
from bs4 import BeautifulSoup
import re
from hashlib import sha256


class Hasher():
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


class ForumParser:
    def get_tor_session(self) -> requests.Session:
        session = requests.session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050',
                           'https': 'socks5h://127.0.0.1:9050'}
        return session

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


def main():
    parser = ForumParser()
    session = parser.get_tor_session()
    response = session.get('https://miped.ru/f/whats-new/posts').text

    parsed_topics = parser.parse_topics(response)

    hasher = Hasher()

    topics_hashes = []
    msg_hashes = []

    for topic in parsed_topics:
        topic_hash = hasher.hash_topic(topic)
        topics_hashes.append(topic_hash)

        topic_response = session.get(topic['topic_url']).text
        parsed_messages = parser.parse_messages(topic['topic_url'], topic_response)

        for message in parsed_messages:
            msg_hash = hasher.hash_msg(message)
            msg_hashes.append(msg_hash)


if __name__ == '__main__':
    main()
