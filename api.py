
import json
from remotezip import RemoteZip
from urllib.request import urlopen


def getJSONData(url: str) -> dict:
    return json.loads(urlopen(url).read())


def getVersionsForDevice(device: str) -> dict:
    url = f'https://api.ipsw.me/v4/device/{device}?type=ipsw'
    return getJSONData(url)


def getVersionURL(version: str, data: dict) -> str:
    for firmware in data['firmwares']:
        if firmware['version'] == version:
            return firmware['url']


def iOSToBuildid(version: str, data: dict) -> str:
    for firmware in data['firmwares']:
        if firmware['version'] == version:
            return firmware['buildid']


def downloadKernelFromURL(url: str) -> None:
    with RemoteZip(url) as f:
        for path in f.filelist:
            if 'kernelcache' in path.filename:
                with open(path.filename, 'wb') as k:
                    k.write(f.read(path.filename))


def getKeysForVersion(device: str, version: str) -> dict:
    data = getVersionsForDevice(device)
    buildid = iOSToBuildid(version, data)
    url = f'https://api.ipsw.me/v4/keys/ipsw/{device}/{buildid}'
    keys = getJSONData(url)
    for key in keys['keys']:
        if key['image'] == 'Kernelcache':
            return key
