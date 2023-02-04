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

    def runCMD(self, cmd: str) -> None:
        if cmd:
            (cmd_in, cmd_out, cmd_err) = self.ssh.exec_command(cmd)
            print('stdout', [o for o in cmd_out])
            print('stderr', [e for e in cmd_err])

    def listDir(self, path: str) -> list:
        sftp = self.ssh.open_sftp()
        contents = sftp.listdir(path)
        sftp.close()
        return contents

    def removeFile(self, path: str) -> None:
        sftp = self.ssh.open_sftp()
        sftp.unlink(path)
        sftp.close()

    def uploadFile(self, file: str, path: str) -> None:
        sftp = self.ssh.open_sftp()
        sftp.put(file, path)
        sftp.close()

    def removeKernel(self) -> None:
        contents = self.listDir('OF32')
        for line in contents:
            if 'kernelcache' in line:
                self.removeFile(f'OF32/{line}')

    def readFile(self, path: str) -> list:
        sftp = self.ssh.open_sftp()
        with sftp.open(path) as f:
            data = f.readlines()
        sftp.close()
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
    client.ssh.close()
    removeLocalKernel()
    print('[*] Parsing offsets')
    return parseOffsets(offsets_raw)


def appendOffsetsJSON(path: Path, offsets: dict) -> None:
    with open(path, 'r+') as f:
        data = json.load(f)
        data.update(offsets)
        f.write(json.dumps(data))


def getAllOffsetsForDevice(address: str, user: str, password: str, device: str) -> dict:
    supported = api.getiOS8And9VersionsForDevice(device)
    offsets = {}
    for version in supported:
        version_offsets = getOffsets(address, user, password, device, version)
        if version_offsets:
            offsets.update(version_offsets)
    return offsets


def getAllOffsets(address: str, user: str, password: str) -> list:
    devices = api.getAllDevices()
    all_offsets = []
    for device in devices:
        device = device['identifier']
        offsets = getAllOffsetsForDevice(address, user, password, device)
        if offsets:
            all_offsets.append(offsets)
    return all_offsets


def main(args: list) -> None:
    if len(args) == 4:
        getAllOffsets(args[1], args[2], args[3])
    else:
        print('Usage: <address> <user> <password>')


if __name__ == '__main__':
    main(sys.argv)
