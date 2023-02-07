
import json
from pathlib import Path


def readFile(path: Path) -> str:
    with open(path) as f:
        return f.read()

def writeFile(path: Path, data: str) -> None:
    with open(path, 'w') as f:
        f.write(data)

def readJSONFile(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)

def writeJSONFile(path: Path, data: dict) -> None:
    with open(path, 'w') as f:
        json.dump(data, f)

def updateJSONFile(path: Path, data: dict) -> None:
    original = json.loads(readFile(path))
    original.update(data)
    writeFile(path, json.dumps(original))
