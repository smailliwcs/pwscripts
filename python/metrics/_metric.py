import abc
import argparse

import pandas as pd

import polyworld as pw


class Metric(abc.ABC):
    _index_label = None
    _value_label = "value"

    @classmethod
    def _parse_run_arg(cls, arg):
        if not pw.run_exists(arg):
            raise argparse.ArgumentTypeError(f"not a Polyworld run: '{arg}'")
        return arg

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("run", metavar="RUN", type=cls._parse_run_arg)
        parser.add_argument("metric", metavar=cls.__name__)

    @classmethod
    def write(cls, data, file):
        data.to_csv(file, header=True)

    @classmethod
    def read(cls, file):
        return pd.read_csv(file, index_col=0, squeeze=True)

    def __init__(self, **kwargs):
        self.run = kwargs["run"]

    @abc.abstractmethod
    def _calculate(self):
        raise NotImplementedError

    def calculate(self):
        indices, values = self._calculate()
        index = pd.Index(indices, name=self._index_label)
        return pd.Series(values, index, name=self._value_label)


class PopulationMetric(Metric, abc.ABC):
    _index_label = "time"


class IndividualMetric(Metric, abc.ABC):
    _index_label = "agent"

    @abc.abstractmethod
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        agents = range(1, pw.get_agent_count(self.run) + 1)
        values = (self._get_value(agent) for agent in agents)
        return agents, values

