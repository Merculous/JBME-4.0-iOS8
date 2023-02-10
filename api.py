
import json
from pathlib import Path
from remotezip import RemoteZip
from urllib.error import HTTPError
from urllib.request import urlopen

import utils

api_path = Path('api')
api_path.mkdir(exist_ok=True)


def getDataFromURL(url: str) -> str:
    try:
        data = urlopen(url).read()
    except HTTPError as e:
        print('[*]', url, e)
    else:
        return data


def getJSONDataFromURL(url: str) -> dict:
    data = getDataFromURL(url)
    if data:
        return json.loads(data)


def getAllDevices() -> Path:
    url = 'https://api.ipsw.me/v4/devices'
    path = Path(f'{api_path.name}/devices.json')
    if not path.exists():
        data = getJSONDataFromURL(url)
        utils.writeJSONFile(path, data)
    return path


def getDeviceData(device: str) -> Path:
    url = f'https://api.ipsw.me/v4/device/{device}?type=ipsw'
    device_path = Path(f'{api_path.name}/{device}')
    device_path.mkdir(parents=True, exist_ok=True)
    device_json = Path(f'{device_path.resolve()}/{device}.json')
    if not device_json.exists():
        data = getJSONDataFromURL(url)
        utils.writeJSONFile(device_json, data)
    return device_json


def getVersionURL(version: str, data: dict) -> str:
    for firmware in data['firmwares']:
        if firmware['version'] == version:
            return firmware['url']


def iOSToBuildid(version: str, data: dict) -> str:
    for firmware in data['firmwares']:
        if firmware['version'] == version:
            return firmware['buildid']


def downloadKernelFromURL(url: str, path: Path) -> None:
    with RemoteZip(url) as f:
        for image in f.filelist:
            if 'kernelcache' in image.filename:
                with open(path, 'wb') as k:
                    k.write(f.read(image.filename))


def getKeysForVersion(device: str, version: str) -> Path:
    device_path = getDeviceData(device)
    data = utils.readJSONFile(device_path)
    buildid = iOSToBuildid(version, data)
    url = f'https://api.ipsw.me/v4/keys/ipsw/{device}/{buildid}'
    keys_path = Path(f'{api_path.name}/{device}/{version}')
    keys_path.mkdir(parents=True, exist_ok=True)
    keys_json = Path(f'{keys_path.resolve()}/keys.json')
    if not keys_json.exists():
        print(f'[*] Gettings keys for {device} {version}')
        keys = getJSONDataFromURL(url)
        if keys:
            utils.writeJSONFile(keys_json.resolve(), keys)
            return keys_json
        else:
            print(f'[*] ipsw.me does not have keys for {version}')


def getiOS8And9VersionsForDevice(device: str) -> list:
    data = utils.readJSONFile(getDeviceData(device))
    versions = []
    for firmware in data['firmwares']:
        version = firmware['version']
        if version.startswith('8') or version.startswith('9'):
            if version not in versions:
                versions.append(version)
    return versions
