
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
        json.dump(data, f)

def updateJSONFile(path: Path, data: dict) -> None:
    if path:
        original = json.loads(readFile(path))
        original.update(data)
        writeFile(path, json.dumps(original))

def appendFileToZPAQArchive(path: Path, archive: Path, method: int) -> None:
    cmd = (
        '/usr/bin/zpaq',
        'a',
        archive.name,
        path.name,
        f'-m{method}'
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
