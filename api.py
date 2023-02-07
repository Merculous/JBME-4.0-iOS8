
import json
from pathlib import Path
from remotezip import RemoteZip
from urllib.error import HTTPError
from urllib.request import urlopen

import utils

api_path = Path('api')
api_path.mkdir()


def getDataFromURL(url: str) -> str:
    try:
        data = urlopen(url).read()
    except HTTPError as e:
        print('[*]', url, e)
    else:
        return data


def getAllDevices() -> Path:
    url = 'https://api.ipsw.me/v4/devices'
    path = Path(f'{api_path.name}/devices.json')
    if not path.exists():
        data = json.loads(getDataFromURL(url))
        utils.writeJSONFile(path, data)
    return path


def getDeviceData(device: str) -> Path:
    url = f'https://api.ipsw.me/v4/device/{device}?type=ipsw'
    path = Path(f'{api_path.name}/{device}.json')
    if not path.exists():
        data = json.loads(getDataFromURL(url))
        utils.writeJSONFile(path, data)
    return path


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


def getKeysForVersion(device: str, version: str) -> Path:
    device_path = getDeviceData(device)
    data = utils.readJSONFile(device_path)
    buildid = iOSToBuildid(version, data)
    url = f'https://api.ipsw.me/v4/keys/ipsw/{device}/{buildid}'
    keys_path = Path(f'{api_path.name}/{device}_{version}_keys.json')
    if not keys_path.exists():
        print(f'[*] Gettings keys for {device} {version}')
        keys = json.loads(getDataFromURL(url))
        if keys:
            utils.writeJSONFile(keys_path, keys)
            return keys_path
        else:
            print(f'[*] ipsw.me does not have keys for values: {device} {version}')



def getiOS8And9VersionsForDevice(device: str) -> list:
    data = utils.readJSONFile(getDeviceData(device))
    versions = []
    for firmware in data['firmwares']:
        version = firmware['version']
        if version.startswith('8') or version.startswith('9'):
            if version not in versions:
                versions.append(version)
    return versions
