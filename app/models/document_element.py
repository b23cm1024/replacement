from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class DocumentElement:
    element_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)