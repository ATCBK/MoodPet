import urllib.request
from typing import Any


def open_without_proxy(request: Any, timeout: float):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(request, timeout=timeout)
