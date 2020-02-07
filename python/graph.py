import functools
import math
import operator


class Graph:
    missing = math.nan
    is_missing = math.isnan

    def __init__(self, vertices):
        self._vertices = set(vertices)
        self._edges = {}
        self._out_edges = {vertex: {} for vertex in self._vertices}
        self._in_edges = {vertex: {} for vertex in self._vertices}

    def __abs__(self):
        return self.map(abs)

    def __getitem__(self, key):
        return self._edges.get(key, self.missing)

    def __setitem__(self, key, value):
        i, j = key
        if self.is_missing(value):
            self._edges.pop(key, None)
            self._out_edges[i].pop(j, None)
            self._in_edges[j].pop(i, None)
        else:
            self._edges[key] = value
            self._out_edges[i][j] = value
            self._in_edges[j][i] = value

    @property
    def vertex_count(self):
        return len(self._vertices)

    @property
    def edge_count(self):
        return len(self._edges)

    def vertices(self):
        return iter(self._vertices)

    def edges(self):
        return iter(self._edges.items())

    def map(self, function, cls=None):
        if cls is None:
            cls = type(self)
        graph = cls(self._vertices)
        for key, value in self._edges.items():
            graph[key] = function(value)
        return graph

    def get_neighbors(self, vertex):
        neighbors = set()
        neighbors.update(self._out_edges[vertex])
        neighbors.update(self._in_edges[vertex])
        neighbors.discard(vertex)
        return neighbors

    def get_neighborhood(self, vertex):
        neighbors = self.get_neighbors(vertex)
        neighborhood = type(self)(neighbors)
        for i in neighbors:
            for j, value in self._out_edges[i].items():
                if j not in neighbors:
                    continue
                neighborhood[i, j] = value
        return neighborhood


class WeightGraph(Graph):
    missing = 0.0
    is_missing = functools.partial(operator.eq, missing)

    @classmethod
    def get_length(cls, weight):
        return 1.0 / abs(weight)

    def get_lengths(self):
        return self.map(self.get_length, LengthGraph)


class LengthGraph(Graph):
    missing = math.inf
    is_missing = functools.partial(operator.eq, missing)

    def __setitem__(self, key, value):
        assert value > 0.0
        super().__setitem__(key, value)

    def get_distances(self):
        for i in self._vertices:
            distances_i = dict.fromkeys(self._vertices, math.inf)
            distances_i[i] = 0.0
            js = set(self._vertices)
            while js:
                j = min(js, key=distances_i.__getitem__)
                js.remove(j)
                distance_ij = distances_i[j]
                if distance_ij == math.inf:
                    break
                for k, length_jk in self._out_edges[j].items():
                    distance_ijk = distance_ij + length_jk
                    if distance_ijk < distances_i[k]:
                        distances_i[k] = distance_ijk
            for j, distance_ij in distances_i.items():
                yield (i, j), distance_ij
