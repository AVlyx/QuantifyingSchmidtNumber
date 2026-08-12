from bound_entangled.cm_otimes_cn import grid_state
from toqito.state_props import is_pure

grid_ex = grid_state(
    (4, 4),
    ((0, 0), (1, 1)),
    ((1, 2), (2, 3)),
    ((0, 3), (3, 0)),
)

print(is_pure(grid_ex))
