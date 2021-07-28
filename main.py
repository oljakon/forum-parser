import requests
from bs4 import BeautifulSoup
import re


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
            topic_name = topic[0].find('a').string
            topic_url = 'https://mipped.com' + topic[0].find('a').get('href')
            last_msg_datetime = re.search(r'datetime=\"(.+?)\"', str(topic[2].find('a'))).group(1)
            replies_number = topic[1].find('dd').string
            if 'K' in replies_number:
                replies_number = int(replies_number[:-1]) * 1000

            topic_data = {
                'topic_name': topic_name,
                'topic_url': topic_url,
                'last_msg_datetime': last_msg_datetime,
                'replies_number': replies_number
            }

            topics_data.append(topic_data)

        return topics_data


def main():
    parser = ForumParser()
    session = parser.get_tor_session()
    response = session.get('https://miped.ru/f/whats-new/posts').text

    parsed_topics = parser.parse_topics(response)


if __name__ == '__main__':
    main()
