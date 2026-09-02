import numpy as np
from pydantic import BaseModel
from enum import Enum
from typing import Optional
import os

from notebook_utils.range_and_canonical import canonical_key, range_canonical

RECORD_FIELDS = ("p", "obj", "separable", "Etl", "obj_max", "Etu")


class Separability(Enum):
    entangled = 0
    inconclusive = 1
    separable = 2


class SdpResult(BaseModel):
    p: float
    separability: Separability
    minSchmidtNumber: int
    objective: float
    Et_lower: list[float]
    objective_max: Optional[float]
    Et_upper: list[Optional[float]]

    def dump_to_jsonl(self, filename: str) -> None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
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


RESULTS_ROOT = "sdp_results"

#: Every sweep lives in one of these subfolders of `sdp_results/`.
FOLDERS = ("vertex", "lam21", "convex", "noise", "SN3", "test", "Parametric")


def result_path(folder: str, filename: str) -> str:
    """Path of a sweep file: `sdp_results/{folder}/{filename}`.

    `folder` names a subfolder of `sdp_results/`; see `FOLDERS`. A `filename` that already
    carries the folder (or the `sdp_results/` prefix) is passed through unchanged, so a path
    printed by one helper can be handed straight back to another.
    """
    filename = filename.replace("\\", "/").lstrip("./")
    if filename.startswith(f"{RESULTS_ROOT}/"):
        return filename
    if folder and not filename.startswith(f"{folder}/"):
        filename = f"{folder}/{filename}"
    return f"{RESULTS_ROOT}/{filename}"


def save_result(
    folder: str,
    filename: str,
    p: float,
    separability: Separability,
    minSchmidtNumber: int,
    objective: float,
    Et_lower: list[float],
    objective_max: Optional[float] = None,
    Et_upper: list[Optional[float]] = [None],
):
    """Append to {filename} in folder sdp_results/{folder} (if it already exists)"""
    res = SdpResult(
        p=canonical_key(p),
        separability=separability,
        objective=objective,
        Et_lower=Et_lower,
        objective_max=_dump_num(objective_max),
        Et_upper=[_dump_num(et) for et in Et_upper],
        minSchmidtNumber=minSchmidtNumber,
    )
    res.dump_to_jsonl(result_path(folder, filename))


def _dump_num(x):
    """NaN is not valid JSON, so it is stored as null."""
    if not x:
        return None
    x = float(x)
    return None if np.isnan(x) else x


def load_all_results(folder: str, filename: str) -> list[SdpResult]:
    path = result_path(folder, filename)
    if not os.path.exists(path):
        return []
    return SdpResult.load_jsonl(path)


def load_results_in_range(folder: str, filename: str, range_: tuple[float, float, float]) -> list[SdpResult]:
    results = load_all_results(folder, filename)
    range_can = range_canonical(range_)
    res = [r for r in results if canonical_key(r.p) in range_can]
    return sorted(res)
