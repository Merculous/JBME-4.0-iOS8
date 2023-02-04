#!/bin/sh

url="https://jailbreak.me"

mkdir payload
wget $url/index.html
wget $url/stage1.bin
cd payload
wget $url/payload/offsets.json
wget $url/payload/tar
wget $url/payload/launchctl
wget $url/payload/Cydia.tar
