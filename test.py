from bound_entangled.c3_otimes_c3 import cross_hatch, tiles_upb
from toqito.state_props import is_separable
import numpy as np

p = 0.35
state = p * cross_hatch() + (1-p) * tiles_upb()

# print(state)

print(np.trace(state))

print(is_separable(state, level=5))