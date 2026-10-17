# action.py
from dataclasses import dataclass


@dataclass
class ProposedAction:
    tool: str
    arguments: str
    context: str = ""
    requester: str = "agent"

    def describe(self) -> str:
        lines = [
            f"Requester: {self.requester}",
            f"Tool: {self.tool}",
            f"Arguments: {self.arguments}",
        ]
        if self.context:
            lines.append(f"Context: {self.context}")
        return "\n".join(lines)