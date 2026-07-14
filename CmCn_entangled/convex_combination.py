def convex_combination(A, B, p_low, p_high, p_step):
    assert p_step > 0
    assert p_low >= 0
    assert p_high <= 1
    while p_low < p_high:
        yield (p_low, p_low * A + (1 - p_low) * B)
        p_low += p_step
