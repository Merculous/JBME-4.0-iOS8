#!/usr/bin/env python3

import paramiko
import sys

from api import getVersionsForDevice, getVersionURL, downloadKernelFromURL


def getKernel(device: str, version: str) -> None:
    data = getVersionsForDevice(device)
    url = getVersionURL(version, data)
    downloadKernelFromURL(url)


def main(args: list) -> None:
    if len(args) == 3:
        getKernel(args[1], args[2])
    else:
        print('Usage: <device> <iOS>')


if __name__ == '__main__':
    main(sys.argv)
