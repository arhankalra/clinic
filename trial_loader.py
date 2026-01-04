from dataclasses import dataclass
from typing import List
import json

@dataclass
class Trial:
    nctid: str
    title: str
    condition: str
    phase: str
    status: str
    city: str
    state: str
    country: str
    summary: str

def load_trials(json_path: str) -> List[Trial]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Trial(**item) for item in data]
