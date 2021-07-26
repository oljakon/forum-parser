import requests


class ForumParser:

    def get_tor_session(self):
        session = requests.session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050',
                           'https': 'socks5h://127.0.0.1:9050'}
        return session


def main():
    parser = ForumParser()
    session = parser.get_tor_session()
    print(session.get('https://miped.ru/f/whats-new/posts').text)


if __name__ == '__main__':
    main()
