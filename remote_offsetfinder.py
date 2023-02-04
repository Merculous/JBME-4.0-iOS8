#!/usr/bin/env python3

import json
import sys

import paramiko
from pathlib import Path

import api


def getDecryptionCMD(device: str, version: str) -> str:
    data = api.getKeysForVersion(device, version)
    if data:
        cmd = (
            '/usr/local/bin/xpwntool',
            'OF32/kernelcache.encrypted',
            'OF32/kernelcache.decrypted',
            f'-iv {data["iv"]}',
            f'-k {data["key"]}'
        )
        return ' '.join(cmd)


def downloadKernel(device: str, version: str) -> None:
    data = api.getDeviceData(device)
    url = api.getVersionURL(version, data)
    api.downloadKernelFromURL(url)


def findKernel() -> str:
    for path in Path().glob('*'):
        if 'kernelcache' in path.name:
            return path.name


def getOF32CMD() -> str:
    cmd = (
        'OF32/OF32',
        'OF32/kernelcache.decrypted',
        '>',
        'OF32/offsets.txt'
    )
    return ' '.join(cmd)


def removeLocalKernel() -> None:
    for path in Path().glob('*'):
        if 'kernelcache' in path.name:
            path.unlink()


class Client:
    def __init__(self, address: str, user: str, password: str) -> None:
        self.address = address
        self.user = user
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(address, username=user, password=password)
        self.sftp = self.ssh.open_sftp()

    def runCMD(self, cmd: str) -> None:
        if cmd:
            (cmd_in, cmd_out, cmd_err) = self.ssh.exec_command(cmd)
            print('STDOUT', [o for o in cmd_out])
            print('STDERR', [e for e in cmd_err])

    def listDir(self, path: str) -> list:
        contents = self.sftp.listdir(path)
        return contents

    def removeFile(self, path: str) -> None:
        self.sftp.unlink(path)

    def uploadFile(self, file: str, path: str) -> None:
        self.sftp.put(file, path)

    def removeKernel(self) -> None:
        contents = self.listDir('OF32')
        for line in contents:
            if 'kernelcache' in line:
                self.removeFile(f'OF32/{line}')

    def readFile(self, path: str) -> list:
        with self.sftp.open(path) as f:
            data = f.readlines()
        return data


def parseOffsets(data: list) -> dict:
    if len(data) > 1:
        uname = data[0].split('"')[1]
        info = {uname: []}
        for line in data:
            if 'pushOffset' in line:
                line = line.split(';')[0][:-1].split('(')[1]
                info[uname].append(line)
        if len(info[uname]) == 18:
            print('[*] Parsing SUCCESS')
            return info
        else:
            print('[*] Parsing FAILED')


def getOffsets(address: str, user: str, password: str, device: str, version: str) -> dict:
    removeLocalKernel()
    print(f'[*] Downloading kernel for {device} {version}')
    downloadKernel(device, version)
    client = Client(address, user, password)
    client.removeKernel()
    print('[*] Uploading kernel')
    client.uploadFile(findKernel(), 'OF32/kernelcache.encrypted')
    print('[*] Decrypting kernel')
    client.runCMD(getDecryptionCMD(device, version))
    print('[*] Running OF32')
    client.runCMD(getOF32CMD())
    client.removeKernel()
    print('[*] Reading offsets')
    offsets_raw = client.readFile('OF32/offsets.txt')
    client.sftp.close()
    client.ssh.close()
    removeLocalKernel()
    print('[*] Parsing offsets')
    return parseOffsets(offsets_raw)


def appendOffsetsJSON(path: Path, offsets: dict) -> None:
    with open(path) as r:
        r_data = json.load(r)
    r_data.update(offsets)
    with open(path, 'w') as w:
        json.dump(r_data, w)


def getAllOffsetsForDevice(address: str, user: str, password: str, device: str) -> dict:
    supported = api.getiOS8And9VersionsForDevice(device)
    offsets = {}
    successfull = []
    for version in supported:
        version_offsets = getOffsets(address, user, password, device, version)
        print('#'*100)
        if version_offsets:
            successfull.append(version)
            offsets.update(version_offsets)
    if successfull:
        print(f'[*] Successfully got offsets for: {successfull}')
        return offsets


def getAllOffsets(address: str, user: str, password: str) -> None:
    devices = api.getAllDevices()
    for device in devices:
        device = device['identifier']
        offsets = getAllOffsetsForDevice(address, user, password, device)
        if offsets:
            appendOffsetsJSON(Path('payload/offsets.json'), offsets)


def main(args: list) -> None:
    if len(args) == 4:
        getAllOffsets(args[1], args[2], args[3])
    else:
        print('Usage: <address> <user> <password>')


if __name__ == '__main__':
    main(sys.argv)
