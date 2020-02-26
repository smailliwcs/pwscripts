import polyworld as pw
from .base import PopulationMetric


class Population(PopulationMetric):
    def _calculate(self):
        table = pw.parse(pw.paths.population(self.run), "Population")
        yield 0, pw.get_initial_agent_count(self.run)
        for row in table.rows():
            yield row["T"], row["Population"]
