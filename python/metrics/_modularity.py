import collections
import itertools
import random

import numpy as np

import polyworld as pw
from brain import Brain
from graph import WeightGraph
from ._metric import IndividualMetric


class Partition:
    def __init__(self, weights):
        self.weights = None
        self.neighbors = None
        self.communities_by_vertex = None
        self.vertices_by_community = None
        self.edge_modularities = None
        self._initialize(weights)
        self.modularity = sum(self.edge_modularities[edge] for edge in self._get_community_edges())

    def _initialize(self, weights):
        self.weights = weights
        self.neighbors = {vertex: [] for vertex in weights.vertices()}
        self.communities_by_vertex = {vertex: vertex for vertex in weights.vertices()}
        self.vertices_by_community = {vertex: {vertex} for vertex in weights.vertices()}
        self.edge_modularities = dict.fromkeys(itertools.product(weights.vertices(), repeat=2), 0.0)
        strength = 0.0
        out_strengths = collections.defaultdict(float)
        in_strengths = collections.defaultdict(float)
        for (i, j), weight_ij in weights.edges():
            if j != i:
                self.neighbors[i].append(j)
                self.neighbors[j].append(i)
            strength += weight_ij
            out_strengths[i] += weight_ij
            in_strengths[j] += weight_ij
        for i, out_strength_i in out_strengths.items():
            for j, in_strength_j in in_strengths.items():
                actual_weight = weights[i, j]
                expected_weight = out_strength_i * in_strength_j / strength
                self.edge_modularities[i, j] = (actual_weight - expected_weight) / strength

    def _get_community_edges(self):
        for community, vertices in self.vertices_by_community.items():
            for edge in itertools.product(vertices, repeat=2):
                yield edge

    def _get_community_neighbors(self, vertex, community):
        neighbors = set(self.vertices_by_community[community])
        neighbors.discard(vertex)
        return neighbors

    def _get_modularity_change(self, vertex, community):
        i = vertex
        js = self._get_community_neighbors(vertex, community)
        return sum(self.edge_modularities[i, j] + self.edge_modularities[j, i] for j in js)

    def _optimize_once(self):
        changed = False
        vertices = list(self.weights.vertices())
        random.shuffle(vertices)
        for vertex in vertices:
            community_old = self.communities_by_vertex[vertex]
            communities_new = set(self.communities_by_vertex[neighbor] for neighbor in self.neighbors[vertex])
            communities_new.discard(community_old)
            if not communities_new:
                continue
            changes = {}
            removal_change = self._get_modularity_change(vertex, community_old)
            for community_new in communities_new:
                addition_change = self._get_modularity_change(vertex, community_new)
                changes[community_new] = addition_change - removal_change
            change_max = max(changes.values())
            if change_max <= 0.0:
                continue
            communities_max = tuple(community for community, change in changes.items() if change == change_max)
            community_max = random.choice(communities_max)
            self.communities_by_vertex[vertex] = community_max
            community_old_vertices = self.vertices_by_community[community_old]
            community_old_vertices.remove(vertex)
            if not community_old_vertices:
                del self.vertices_by_community[community_old]
            self.vertices_by_community[community_max].add(vertex)
            self.modularity += change_max
            changed = True
        return changed

    def optimize(self):
        changed = False
        while self._optimize_once():
            changed = True
        return changed

    def combine(self):
        weights = WeightGraph(set(self.vertices_by_community))
        for (i, j), weight_ij in self.weights.edges():
            weights[self.communities_by_vertex[i], self.communities_by_vertex[j]] += weight_ij
        self._initialize(weights)


_THRESHOLD = 1e-6


def get_partition(weights, threshold=_THRESHOLD):
    if weights.vertex_count <= 1:
        return 0.0
    partition = Partition(abs(weights))
    modularity = partition.modularity
    while partition.optimize():
        if partition.modularity - modularity < threshold:
            break
        modularity = partition.modularity
        partition.combine()
    return partition


def get_modularity(weights, threshold=_THRESHOLD):
    return get_partition(weights, threshold).modularity


class Modularity(IndividualMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("stage", metavar="STAGE", choices=tuple(stage.value for stage in pw.Stage))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stage = pw.Stage(kwargs["stage"])

    def _get_value(self, agent):
        brain = Brain.read(self.run, agent, self.stage)
        if brain is None:
            return np.ma.masked
        return get_modularity(brain.weights)
