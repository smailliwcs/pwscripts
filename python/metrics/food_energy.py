import polyworld as pw
from .base import PopulationMetric


class FoodEnergy(PopulationMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("type", metavar="TYPE")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = kwargs["type"]

    def _calculate(self):
        table = pw.parse(pw.paths.food_energy(self.run), "FoodEnergy")
        for row in table.rows():
            yield row["Timestep"], row[self.type]

    def _write_arguments(self, file):
        file.write(f"# TYPE = {self.type}\n")
