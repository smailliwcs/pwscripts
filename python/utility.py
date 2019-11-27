import math


def mean(values):
    count = 0
    sum_ = 0
    for value in values:
        count += 1
        sum_ += value
    if not count:
        return math.nan
    return sum_ / count


__all__ = (
    "mean",
)
