import numpy as np
from pydantic import BaseModel
from enum import Enum
from typing import Optional
import os

from utils.range_and_canonical import canonical_key, range_canonical

RECORD_FIELDS = ("p", "obj", "separable", "Etl", "obj_max", "Etu")


class Separability(Enum):
    entangled = 0
    inconclusive = 1
    separable = 2


class SdpResult(BaseModel):
    p: float
    separability: Separability
    minSchmidtNumber: int
    objective: Optional[float]
    Et_lower: Optional[float]
    objective_max: Optional[float]
    Et_upper: Optional[float]

    def dump_to_jsonl(self, filename: str) -> None:
        if not os.path.exists(filename):
            with open(filename, "a") as f:
                f.write(self.model_dump_json() + "\n")
                f.flush()
                os.fsync(f.fileno())
            return
        res = SdpResult.load_jsonl(filename)
        res.append(self)
        res.sort()
        string_val = "\n".join([r.model_dump_json() for r in res]) + "\n"
        with open(filename, "w") as f:
            f.write(string_val)
            f.flush()
            os.fsync(f.fileno())

    @classmethod
    def load_jsonl(cls, filename: str) -> list["SdpResult"]:
        with open(filename) as f:
            return [cls.model_validate_json(line) for line in f if line.strip()]

    def __lt__(self, other: "SdpResult") -> bool:
        return self.p < other.p


def save_result(
    filename: str,
    p: float,
    separability: Separability,
    minSchmidtNumber: int,
    objective: Optional[float],
    Et_lower: Optional[float],
    objective_max: Optional[float] = None,
    Et_upper: Optional[float] = None,
):
    """Append to {filename} in folder sdp_results (if it already exists)"""
    res = SdpResult(
        p=canonical_key(p),
        separability=separability,
        objective=_dump_num(objective),
        Et_lower=_dump_num(Et_lower),
        objective_max=_dump_num(objective_max),
        Et_upper=_dump_num(Et_upper),
        minSchmidtNumber=minSchmidtNumber,
    )
    res.dump_to_jsonl(f"sdp_results/{filename}")


def _dump_num(x):
    """NaN is not valid JSON, so it is stored as null."""
    if not x:
        return None
    x = float(x)
    return None if np.isnan(x) else x


def load_results_in_range(filename: str, range_: tuple[float, float, float]):
    if not filename.startswith("sdp_results") or filename.startswith("./sdp_results"):
        filename = f"sdp_results/{filename}"

    results = SdpResult.load_jsonl(filename)
    range_can = range_canonical(range_)

    res = [r for r in results if canonical_key(r.p) in range_can]
    return sorted(res)
