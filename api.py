
import json
from remotezip import RemoteZip
from urllib.error import HTTPError
from urllib.request import urlopen


def getJSONData(url: str) -> dict:
    try:
        data = urlopen(url).read()
    except HTTPError as e:
        print('[*]', url, e)
    else:
        return json.loads(data)


def getDeviceData(device: str) -> dict:
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
    data = getDeviceData(device)
    buildid = iOSToBuildid(version, data)
    url = f'https://api.ipsw.me/v4/keys/ipsw/{device}/{buildid}'
    keys = getJSONData(url)
    print(f'[*] Gettings keys for {device} {version}')
    if keys:
        for key in keys['keys']:
            if key['image'] == 'Kernelcache':
                return key
    else:
        print(f'[*] ipsw.me does not have keys for values: {device} {version}')


def getiOS8And9VersionsForDevice(device: str) -> list:
    data = getDeviceData(device)
    versions = []
    for firmware in data['firmwares']:
        version = firmware['version']
        if version.startswith('8') or version.startswith('9'):
            if version not in versions:
                versions.append(version)
    return versions


def getAllDevices() -> dict:
    url = 'https://api.ipsw.me/v4/devices'
    return getJSONData(url)
