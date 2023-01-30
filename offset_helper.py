#!/usr/bin/env python3

import json
from pathlib import Path

JSON_path = Path('payload/offsets.json')


def readJSONFile(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def parseJSONData(data: dict) -> None:
    for uname in data:
        print(uname)
        for offset in data[uname]:
            print(offset)
        print(f'n of offsets: {len(data[uname])}')
    print(f'n of versions supported: {len(data)}')


def main() -> None:
    JSON_data = readJSONFile(JSON_path)
    parseJSONData(JSON_data)


if __name__ == '__main__':
    main()
