from .base import PopulationMetric, parse_range_arg


class Diversity(PopulationMetric):
    has_run_arg = False

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("data", metavar="DATA")
        parser.add_argument("genes", metavar="GENES", type=parse_range_arg)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = kwargs["data"]
        self.genes = kwargs["genes"]

    def get_data(self):
        if self.genes.is_finite():
            columns = ["time", *(f"value{index}" for index in self.genes)]
            return self.read(self.data, usecols=columns, squeeze=False)
        else:
            data = self.read(self.data, squeeze=False)
            columns = [f"value{index}" for index in range(len(data.columns)) if index in self.genes]
            return data[columns]

    def _calculate(self):
        return self.get_data().mean(axis=1)
