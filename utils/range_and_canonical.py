import numpy as np

P_DECIMALS = 10


def range_canonical(range_: tuple[float, float, float]):
    start, end, step = range_
    return [canonical_key(p) for p in np.arange(start, end + step / 2.0, step)]


def canonical_key(p):
    """Canonical key for a parameter value."""
    return round(float(p), P_DECIMALS)
