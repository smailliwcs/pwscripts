import polyworld as pw
from .base import IndividualMetric


class Lifespan(IndividualMetric):
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        table = pw.parse(pw.paths.lifespans(self.run), "LifeSpans")
        for row in table.rows():
            agent = row["Agent"]
            value = None if row["DeathReason"] == "SIMEND" else row["DeathStep"] - row["BirthStep"]
            yield agent, value
