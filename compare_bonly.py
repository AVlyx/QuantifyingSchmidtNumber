"""Two-sided (copies of the pair, SDP_utils.sdp.SDP) vs one-sided (copies of Bob only,
SDP_utils.sdp_bonly.SDP_bonly) weak-Schur roof SDPs.

usage:  python compare_bonly.py iso      # 3x3 isotropic, height 3 (SN>2), k=3; exact threshold F=2/3
        python compare_bonly.py r1       # Horodecki / Tiles + white noise, height 2 (entanglement), k=2,3
"""
import sys
import time
import numpy as np
from toqito.states import isotropic as isoA, horodecki, tile
from SDP_utils.sdp import SDP
from SDP_utils.sdp_bonly import SDP_bonly


def isotropic(F):
    return np.real(isoA(3, (9 * F - 1) / 8))


def timed(f):
    t = time.time()
    v = f()
    return v, time.time() - t


mode = sys.argv[1]

if mode == "iso":
    for F in [1.0, 0.9, 0.8, 0.75, 0.7, 0.68, 2 / 3, 0.65]:
        rho = isotropic(F)
        (two, _), t2 = timed(lambda: SDP(3, 3, rho, (3, 3), real=True))
        (one, _), t1 = timed(lambda: SDP_bonly(3, 3, rho, (3, 3), real=True))
        (oner, _), t1r = timed(lambda: SDP_bonly(3, 3, rho, (3, 3), real=True, reduction=True))
        print(f"iso F={F:.4f}: two-sided k=3 {two:+.3e} ({t2:.0f}s) | B-only k=3 {one:+.3e} ({t1:.0f}s) | B-only+reduction {oner:+.3e} ({t1r:.0f}s)", flush=True)

elif mode == "r1":
    fams = {"horodecki a=.5": (horodecki(0.5, [3, 3]), [1.0, 0.98, 0.96, 0.95])}
    T = np.column_stack([tile(i) for i in range(5)])
    fams["tile"] = ((np.eye(9) - T @ T.T) / 4, [1.0, 0.95, 0.9, 0.88])
    for name, (rho0, ps) in fams.items():
        for p in ps:
            rho = p * rho0 + (1 - p) * np.eye(9) / 9
            two2, _ = SDP(2, 2, rho, (3, 3), real=True)
            one2, _ = SDP_bonly(2, 2, rho, (3, 3), real=True)
            one2c, _ = SDP_bonly(2, 2, rho, (3, 3), real=True, extra_cut=True)
            one3, _ = SDP_bonly(2, 3, rho, (3, 3), real=True)
            one3c, _ = SDP_bonly(2, 3, rho, (3, 3), real=True, extra_cut=True)
            print(f"{name} p={p}: two-sided k=2 {two2:+.3e} | B-only k=2 {one2:+.3e} (+A|BB cut {one2c:+.3e}) | B-only k=3 {one3:+.3e} (+cut {one3c:+.3e})", flush=True)

elif mode == "r1k3":
    rho0 = horodecki(0.5, [3, 3])
    for p in [float(x) for x in sys.argv[2].split(",")]:
        rho = p * rho0 + (1 - p) * np.eye(9) / 9
        (two3, _), t = timed(lambda: SDP(2, 3, rho, (3, 3), real=True, exact_height=False))
        print(f"horodecki a=.5 p={p}: two-sided k=3 (height>=2) {two3:+.3e} ({t:.0f}s)", flush=True)

elif mode == "k2":
    T = np.column_stack([tile(i) for i in range(5)])
    fams = {"tile": ((np.eye(9) - T @ T.T) / 4, [1.0, 0.95, 0.9, 0.88, 0.87])}
    fams["isotropic (height 2, exact thr F=1/3)"] = (None, [0.6, 0.45, 0.4, 0.36, 0.34])
    for name, (rho0, ps) in fams.items():
        for p in ps:
            rho = isotropic(p) if rho0 is None else p * rho0 + (1 - p) * np.eye(9) / 9
            (two2, _), t2 = timed(lambda: SDP(2, 2, rho, (3, 3), real=True))
            (one2, _), t1 = timed(lambda: SDP_bonly(2, 2, rho, (3, 3), real=True))
            try:
                one2c, _ = SDP_bonly(2, 2, rho, (3, 3), real=True, extra_cut=True)
            except Exception as e:
                one2c = float("inf")
            print(f"{name} p={p}: two-sided k=2 {two2:+.3e} ({t2:.0f}s) | B-only k=2 {one2:+.3e} ({t1:.0f}s) | B-only k=2 + A|BB cut {one2c:+.3e}", flush=True)
