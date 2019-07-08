import argparse
import re
from socket import gaierror, gethostbyname
from urllib.parse import urlparse
import requests
from json.decoder import JSONDecodeError


re_url = re.compile(
    r'^https?://'  # http:// or https://
    # domain...
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def get_com(url):
    try:
        p = urlparse(url)
        return p.netloc
    except:
        return None


def get_ip(dom):
    try:
        ip = gethostbyname(dom)
        return ip
    except gaierror as e:
        return None


class WPcheck:
    def __init__(self, http="http"):
        self.http = http

    def __call__(self, value):
        _value = value
        if value.split("://")[0] not in ("http", "https"):
            value = "http://"+value
        dom = get_com(value)
        if not dom:
            raise argparse.ArgumentTypeError(
                "'{}' no es una url válida".format(_value))
        ip = get_ip(dom)
        if not ip:
            raise argparse.ArgumentTypeError(
                "'{}' no es alcanzable".format(dom))
        url = value
        if url.endswith("/"):
            url = url[:1]
        url = url + "/?rest_route=/"
        r = requests.get(url)
        try:
            r.json()
        except JSONDecodeError:
            raise argparse.ArgumentTypeError(
                "'{}' no es un blog wordpress o no tiene la api wp-json habilitada".format(dom))
        return value
