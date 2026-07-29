from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Chunk:

    title: str

    content: str

    metadata: Dict[str, Any] = field(default_factory=dict)