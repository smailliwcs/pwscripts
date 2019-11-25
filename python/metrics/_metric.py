import abc
import argparse

import numpy as np
import pandas as pd

import polyworld as pw


class Metric(abc.ABC):
    _x_label = None
    _y_label = "value"

    @classmethod
    def _parse_run_arg(cls, arg):
        if not pw.run_exists(arg):
            raise argparse.ArgumentTypeError(f"not a Polyworld run: '{arg}'")
        return arg

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("run", metavar="RUN", type=cls._parse_run_arg)
        parser.add_argument("metric", metavar=cls.__name__)

    def __init__(self, **kwargs):
        self.run = kwargs["run"]

    @abc.abstractmethod
    def _calculate(self):
        raise NotImplementedError

    def calculate(self):
        x, y = self._calculate()
        return pd.DataFrame({
            self._x_label: x,
            self._y_label: y
        })


class IndividualMetric(Metric, abc.ABC):
    _x_label = "agent"

    @abc.abstractmethod
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        agents = np.array(pw.get_agents(self.run))
        values = np.ma.empty(agents.shape)
        for index, agent in enumerate(agents):
            values[index] = self._get_value(agent)
        return agents, values


class PopulationMetric(Metric, abc.ABC):
    _x_label = "time"
