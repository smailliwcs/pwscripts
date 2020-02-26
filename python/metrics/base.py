import abc
import argparse
import math

import pandas as pd

import polyworld as pw


class Metric(abc.ABC):
    index_label = None
    value_label = "value"

    @classmethod
    def parse_run_arg(cls, arg):
        if not pw.run_exists(arg):
            raise argparse.ArgumentTypeError(f"not a Polyworld run: '{arg}'")
        return arg

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("run", metavar="RUN", type=cls.parse_run_arg)
        parser.add_argument("metric", metavar=cls.__name__)

    @classmethod
    def read(cls, file):
        return pd.read_csv(file, sep=" ", index_col=0, squeeze=True, comment="#")

    def __init__(self, **kwargs):
        self.arguments = kwargs
        self.run = kwargs["run"]

    @abc.abstractmethod
    def _calculate(self):
        raise NotImplementedError

    def calculate(self):
        values = pd.Series(dict(self._calculate()), name=self.value_label)
        values.index.name = self.index_label
        return values

    def _write_arguments(self, file):
        pass

    def write(self, file, values=None):
        if values is None:
            values = self.calculate()
        self._write_arguments(file)
        values.to_csv(file, sep=" ", na_rep=str(math.nan), header=True)


class PopulationMetric(Metric, abc.ABC):
    index_label = "time"


class IndividualMetric(Metric, abc.ABC):
    class Aggregator(PopulationMetric):
        def __init__(self, run, values, function):
            super().__init__(run=run)
            if isinstance(function, str):
                function = getattr(pd.Series, function)
            self.values = values
            self.function = function

        def _calculate(self):
            for time, agents in pw.get_populations(self.run):
                yield time, self.function(self.values.loc[agents])

    index_label = "agent"
    aggregator = "mean"

    @abc.abstractmethod
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        for agent in pw.get_agents(self.run):
            yield agent, self._get_value(agent)

    def aggregate(self, values=None, function=None):
        if values is None:
            values = self.calculate()
        if function is None:
            function = self.aggregator
        return self.Aggregator(self.run, values, function).calculate()
