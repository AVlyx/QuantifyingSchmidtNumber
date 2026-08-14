import numpy as np

P_DECIMALS = 10


def range_canonical(range_: tuple[float, float, float]) -> list[float]:
    start, end, step = range_
    if step == 0:
        return [canonical_key(start)]
    length = max(0, int(np.ceil((end - start) / step)) + 1)
    return [canonical_key(start + i * step) for i in range(length) if canonical_key(start + i * step) <= end]


def canonical_key(p):
    """Canonical key for a parameter value."""
    return round(float(p), P_DECIMALS)
