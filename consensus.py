# consensus.py
from dataclasses import dataclass
from typing import Literal

import jevlang

import perspectives
from action import ProposedAction

Verdict = Literal["allow", "human", "block"]


@dataclass
class Perspective:
    name: str
    verdict: Verdict
    score: float
    label: str
    confidence: float


@dataclass
class ConsensusResult:
    verdict: Verdict
    perspectives: list[Perspective]
    agreement: int
    reason: str
    details: str


def gather_perspectives(action: ProposedAction) -> list[Perspective]:
    text = action.describe()

    # Call 1: Safety
    s = perspectives.ask_safety(text)
    safety_safe = float(s.safe_to_run)
    safety_sev = float(s.severity)
    if safety_safe >= 0.7 and safety_sev < 2.0:
        safety_verdict: Verdict = "allow"
    elif safety_safe >= 0.4 or safety_sev < 3.5:
        safety_verdict = "human"
    else:
        safety_verdict = "block"

    # Call 2: Legitimacy
    leg = perspectives.ask_legitimacy(text)
    legit_ok = float(leg.is_authorized)
    legit_surprise = float(leg.surprise_level)
    if legit_ok >= 0.7 and legit_surprise < 1.5:
        legit_verdict: Verdict = "allow"
    elif legit_ok >= 0.4:
        legit_verdict = "human"
    else:
        legit_verdict = "block"

    # Call 3: Adversarial
    adv = perspectives.ask_adversarial(text)
    attack = float(adv.looks_like_attack)
    attack_type = str(adv.attack_type)
    if attack < 0.3 and attack_type == "none":
        attack_verdict: Verdict = "allow"
    elif attack < 0.7:
        attack_verdict = "human"
    else:
        attack_verdict = "block"

    return [
        Perspective(
            "safety", safety_verdict, safety_sev, "severity",
            s.severity.confidence,
        ),
        Perspective(
            "legitimacy", legit_verdict, legit_surprise, "surprise",
            leg.surprise_level.confidence,
        ),
        Perspective(
            "adversarial", attack_verdict, attack, attack_type,
            adv.attack_type.confidence,
        ),
    ]


def decide(action: ProposedAction) -> ConsensusResult:
    ps = gather_perspectives(action)

    allows = sum(1 for p in ps if p.verdict == "allow")
    humans = sum(1 for p in ps if p.verdict == "human")
    blocks = sum(1 for p in ps if p.verdict == "block")

    detail = "\n".join(
        f"  {p.name:12s} -> {p.verdict:5s}  "
        f"({p.label}={p.score:.2f}, conf={p.confidence:.2f})"
        for p in ps
    )

    if allows == 3:
        return ConsensusResult(
            "allow", ps, 3,
            "Unanimous: all three perspectives approved.", detail,
        )

    if blocks >= 1:
        return ConsensusResult(
            "block", ps, allows,
            f"Blocked: {blocks} of 3 perspectives flagged this as unsafe.",
            detail,
        )

    if humans >= 1:
        return ConsensusResult(
            "human", ps, allows,
            f"Disagreement: {allows} allow, {humans} escalate. "
            "Routing to human.",
            detail,
        )

    return ConsensusResult(
        "human", ps, allows,
        "No consensus reached. Routing to human.", detail,
    )