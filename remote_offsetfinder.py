#!/usr/bin/env python3

import sys

import paramiko
from pathlib import Path

from api import downloadKernelFromURL, getVersionsForDevice, getVersionURL, getKeysForVersion


def getDecryptionCMD(device: str, version: str) -> str:
    data = getKeysForVersion(device, version)
    cmd = (
        '/usr/local/bin/xpwntool',
        'OF32/kernelcache.encrypted',
        'OF32/kernelcache.decrypted',
        f'-iv {data["iv"]}',
        f'-k {data["key"]}'
    )
    return ' '.join(cmd)


def downloadKernel(device: str, version: str) -> None:
    data = getVersionsForDevice(device)
    url = getVersionURL(version, data)
    downloadKernelFromURL(url)


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
        (cmd_in, cmd_out, cmd_err) = self.ssh.exec_command(cmd)
        stdout = [out for out in cmd_out]
        stderr = [err for err in cmd_err]
        print(stdout)
        print(stderr)

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


def getOffsets(address: str, user: str, password: str, device: str, version: str) -> list:
    removeLocalKernel()
    downloadKernel(device, version)
    client = Client(address, user, password)
    client.removeKernel()
    client.uploadFile(findKernel(), 'OF32/kernelcache.encrypted')
    client.runCMD(getDecryptionCMD(device, version))
    client.runCMD(getOF32CMD())
    client.removeKernel()
    offsets = client.readFile('OF32/offsets.txt')
    client.ssh.close()
    removeLocalKernel()
    return offsets


def parseOffsets(data: list) -> dict:
    uname = data[3].split('"')[1]
    info = {uname: []}
    for line in data:
        if 'pushOffset' in line:
            line = line.split(';')[0][:-1].split('(')[1]
            info[uname].append(line)
    return info


def main(args: list) -> None:
    if len(args) == 6:
        offsets = getOffsets(args[1], args[2], args[3], args[4], args[5])
        print(parseOffsets(offsets))
    else:
        print('Usage: <address> <user> <password> <device> <ios>')


if __name__ == '__main__':
    main(sys.argv)
