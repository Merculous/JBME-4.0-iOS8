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


def getKernel(device: str, version: str) -> None:
    data = getVersionsForDevice(device)
    url = getVersionURL(version, data)
    downloadKernelFromURL(url)


def findKernel() -> str:
    for path in Path().glob('*'):
        if 'kernelcache' in path.name:
            return path


def getOF32CMD() -> str:
    cmd = (
        'OF32/OF32',
        'OF32/kernelcache.decrypted'
    )
    return ' '.join(cmd)


def getOffsets(address: str, user: str, password: str, device: str, version: str) -> list:
    getKernel(device, version)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(address, username=user, password=password)
    sftp = ssh.open_sftp()
    sftp.put(findKernel(), 'OF32/kernelcache.encrypted')
    ssh.exec_command(getDecryptionCMD(device, version))
    (cmd_in, cmd_out, cmd_err) = ssh.exec_command(getOF32CMD())
    offsets = [o for o in cmd_out]
    sftp.close()
    ssh.close()
    return offsets


def main(args: list) -> None:
    if len(args) == 6:
        offsets = getOffsets(args[1], args[2], args[3], args[4], args[5])
        print(offsets)
    else:
        print('Usage: <address> <user> <password> <device> <ios>')


if __name__ == '__main__':
    main(sys.argv)
