
import json
import subprocess
from pathlib import Path


def readFile(path: Path) -> str:
    if path:
        with open(path) as f:
            return f.read()


def writeFile(path: Path, data: str) -> None:
    with open(path, 'w') as f:
        f.write(data)


def readJSONFile(path: Path) -> dict:
    if path:
        with open(path) as f:
            return json.load(f)


def writeJSONFile(path: Path, data: dict) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=1, sort_keys=True)


def updateJSONFile(path: Path, data: dict) -> None:
    if path.exists():
        original = json.loads(readFile(path))
        original.update(data)
        writeFile(path, json.dumps(original, indent=1, sort_keys=True))
    else:
        writeFile(path, json.dumps(data, indent=1, sort_keys=True))


def appendFileToZPAQArchive(path: Path, archive: Path) -> None:
    cmd = (
        '/usr/bin/zpaq',
        'a',
        archive.name,
        path.name
    )
    subprocess.run(cmd)


def extractFileFromZPAQArchive(path: Path, archive: Path) -> None:
    cmd = (
        '/usr/bin/zpaq',
        'x',
        archive.name,
        path.name
    )
    subprocess.run(cmd)
