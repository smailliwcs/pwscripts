import collections

import polyworld as pw
from .base import PopulationMetric


class FoodConsumption(PopulationMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("type", metavar="TYPE")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = kwargs["type"]

    def _calculate(self):
        values = collections.defaultdict(float)
        table = pw.parse(pw.paths.food_consumption(self.run), "FoodConsumption")
        for row in table.rows():
            if row["FoodType"] == self.type:
                values[row["Timestep"]] += row["EnergyRaw"]
        for time in pw.get_times(self.run):
            yield time, values[time]

    def _write_arguments(self, file):
        file.write(f"# TYPE = {self.type}\n")
