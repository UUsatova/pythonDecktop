import json
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


def build_query_url(base_url: str, params: dict) -> str:
    parsed = urlparse(base_url)
    query = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    return urlunparse(parsed._replace(query=query))


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "Tkinter-Report/1.0"})
    with urlopen(req, timeout=20) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))
