import enum


class Layer(enum.Enum):
    ALL = "all"
    INPUT = "input"
    PROCESSING = "processing"
    OUTPUT = "output"
    INTERNAL = "internal"
