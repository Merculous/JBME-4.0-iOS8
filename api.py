
import json
from remotezip import RemoteZip
from urllib.request import urlopen


def getVersionsForDevice(device: str) -> dict:
    url = f'https://api.ipsw.me/v4/device/{device}?type=ipsw'
    return json.loads(urlopen(url).read())


def getVersionURL(version: str, data: dict) -> str:
    for firmware in data['firmwares']:
        if firmware['version'] == version:
            return firmware['url']


def downloadKernelFromURL(url: str):
    with RemoteZip(url) as f:
        for path in f.filelist:
            if 'kernelcache' in path.filename:
                with open(path.filename, 'wb') as k:
                    k.write(f.read(path.filename))
