#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import paramiko

import api
import utils


def getDecryptionCMD(device: str, version: str) -> str:
    keys_path = api.getKeysForVersion(device, version)
    data = utils.readJSONFile(keys_path)
    if data:
        for key in data['keys']:
            if key['image'] == 'Kernelcache':
                cmd = (
                    '/usr/local/bin/xpwntool',
                    'OF32/kernelcache.encrypted',
                    'OF32/kernelcache.decrypted',
                    f'-iv {key["iv"]}',
                    f'-k {key["key"]}'
                )
                return ' '.join(cmd)


def downloadKernel(device: str, version: str) -> Path:
    device_path = api.getDeviceData(device)
    data = utils.readJSONFile(device_path)
    if data:
        url = api.getVersionURL(version, data)
        kernel_str = 'kernelcache.encrypted'
        kernel_path = Path(f'kernels/{device}/{version}')
        kernel_path.mkdir(parents=True, exist_ok=True)
        kernel_encrypted = Path(f'{kernel_path.resolve()}/{kernel_str}')
        api.downloadKernelFromURL(url, kernel_encrypted.resolve())
        return kernel_encrypted


def getOF32CMD() -> str:
    return 'OF32/OF32 OF32/kernelcache.decrypted'


class Client:
    def __init__(self, address: str, user: str, password: str) -> None:
        self.address = address
        self.user = user
        self.password = password
        #################################
        self.ssh = paramiko.SSHClient()
        #################################
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(address, username=user, password=password)
        #################################
        self.sftp = self.ssh.open_sftp()
        #################################

    def runCMD(self, cmd: str) -> tuple:
        if cmd:
            (cmd_in, cmd_out, cmd_err) = self.ssh.exec_command(cmd)
            output = ([o for o in cmd_out], [e for e in cmd_err])
            print('STDOUT:', output[0])
            print('STDERR:', output[1])
            return output

    def listDir(self, path: str) -> list:
        contents = self.sftp.listdir(path)
        return contents

    def removeFile(self, path: str) -> None:
        self.sftp.unlink(path)

    def uploadFile(self, file: Path, path: str) -> None:
        self.sftp.put(file.resolve(), path)

    def downloadFile(self, file: str, path: Path) -> None:
        self.sftp.get(file, path.resolve())

    def removeKernels(self) -> None:
        contents = self.listDir('OF32')
        for line in contents:
            if 'kernelcache' in line:
                self.removeFile(f'OF32/{line}')

    def readFile(self, path: str) -> list:
        with self.sftp.open(path) as f:
            data = f.readlines()
        return data


def parseOF32Output(data: list) -> dict:
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


def initHomeDepotJSON(device: str, version: str, data: dict) -> None:
    info = {device: {version: data}}
    path = Path('HomeDepot.json')
    if path.exists():
        data = utils.readJSONFile(path)
        for identifier in data:
            if identifier == device:
                data[device][version] = info[device][version]
        utils.writeJSONFile(path, data)
    else:
        utils.writeJSONFile(path, info)


def parseOffsets(device: str, version: str, of32_output: list) -> None:
    if of32_output:
        print('[*] Parsing offsets')
        parsed_offests = parseOF32Output(of32_output)
        if parsed_offests:
            print('[*] Writing offsets to json files')
            utils.updateJSONFile(Path('payload/offsets.json'), parsed_offests)
            initHomeDepotJSON(device, version, parsed_offests)


def getOffsets(address: str, user: str, password: str, device: str, version: str) -> None:
    print(f'[*] Downloading kernel for {device} {version}')
    kernel_path = Path(f'kernels/{device}/{version}')
    kernel_encrypted = downloadKernel(device, version)
    client = Client(address, user, password)
    client.removeKernels()
    print('[*] Uploading kernel')
    client.uploadFile(kernel_encrypted.resolve(), 'OF32/kernelcache.encrypted')
    print('[*] Decrypting kernel')
    client.runCMD(getDecryptionCMD(device, version))
    print('[*] Running OF32')
    offsets_raw = client.runCMD(getOF32CMD())[0]
    kernel_decrypted = Path(f'{kernel_path.resolve()}/kernelcache.decrypted')
    client.downloadFile('OF32/kernelcache.encrypted', kernel_decrypted)
    client.removeKernels()
    parseOffsets(device, version, offsets_raw)
    #################################
    client.sftp.close()  # IMPORTANT
    client.ssh.close()  # IMPORTANT
    #################################
    print('#'*100)


def getAllOffsetsForDevice(address: str, user: str, password: str, device: str) -> None:
    supported = api.getiOS8And9VersionsForDevice(device)
    if supported:
        for version in supported:
            getOffsets(address, user, password, device, version)


def getAllOffsets(address: str, user: str, password: str) -> None:
    devices_path = api.getAllDevices()
    data = utils.readJSONFile(devices_path)
    platforms_supported = (
        's5l8940x',
        's5l8942x',
        's5l8945x',
        's5l8947x',
        's5l8950x',
        's5l8955x'
    )
    if data:
        for platform in platforms_supported:
            for device in data:
                name = device['identifier']
                if device['platform'] == platform:
                    getAllOffsetsForDevice(address, user, password, name)
                else:
                    print(f'Skipping device: {name}')


def main(args: list) -> None:
    if len(args) == 4:
        getAllOffsets(args[1], args[2], args[3])
    else:
        print('Usage: <address> <user> <password>')


if __name__ == '__main__':
    main(sys.argv)
