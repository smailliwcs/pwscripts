import polyworld as pw
from .base import PopulationMetric


class EventCount(PopulationMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("type", metavar="TYPE", choices=tuple(type_.value for type_ in pw.Event.Type))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = pw.Event.Type(kwargs["type"])

    def _calculate(self):
        events = pw.get_events(self.run)
        for time in pw.get_times(self.run):
            yield time, sum(1 for event in events[time] if event.type == self.type)

    def _write_arguments(self, file):
        file.write(f"# TYPE = {self.type.value}\n")
