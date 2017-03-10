import random
import utility

# https://en.wikipedia.org/wiki/Dijkstra's_algorithm
class Distance(object):
    inf = float("inf")
    
    @staticmethod
    def calculate(W):
        N = len(W)
        L = {}
        for i in xrange(N):
            L[i] = {}
            for j in xrange(N):
                if j == i:
                    continue
                W_ij = W[i][j]
                if W_ij is not None and W_ij != 0.0:
                    L[i][j] = 1.0 / abs(W_ij)
        D = {}
        for i in xrange(N):
            D[i] = {}
            for j in xrange(N):
                if j == i:
                    D[i][j] = 0.0
                else:
                    D[i][j] = Distance.inf
            Q = set(xrange(N))
            while len(Q) > 0:
                j = min(Q, key = lambda j: D[i][j])
                for k, L_jk in L[j].iteritems():
                    D_ijk = D[i][j] + L_jk
                    if D_ijk < D[i][k]:
                        D[i][k] = D_ijk
                Q.remove(j)
        return D
    
    def __init__(self):
        raise NotImplementedError

class Efficiency(object):
    @staticmethod
    def calculate(D):
        N = len(D)
        if N <= 1:
            return 0.0
        sum_D_inv = 0.0
        for i in xrange(N):
            for j in xrange(N):
                if j == i:
                    continue
                sum_D_inv += 1.0 / D[i][j]
        return sum_D_inv / (N * (N - 1))
    
    def __init__(self):
        raise NotImplementedError

# https://arxiv.org/abs/0803.0476
class Modularity(object):
    dQ_min = 1e-6
    
    class State(object):
        def __init__(self, W):
            self.W = W
            self.N = len(W)
            self.C = range(self.N)
            self.E = [None] * self.N
            for i in xrange(self.N):
                self.E[i] = set()
            self.S = 0.0
            self.S_out = [0.0] * self.N
            self.S_in = [0.0] * self.N
            for i in xrange(self.N):
                for j in xrange(self.N):
                    W_ij = W[i][j]
                    if W_ij == 0.0:
                        continue
                    self.E[i].add(j)
                    self.E[j].add(i)
                    self.S += W_ij
                    self.S_out[i] += W_ij
                    self.S_in[j] += W_ij
        
        def get_Q_ij(self, i, j):
            return (1.0 / self.S) * (self.W[i][j] - self.S_out[i] * self.S_in[j] / self.S)
        
        def get_dQ(self, i, C_i):
            if C_i is None:
                sign = -1
                C_i = self.C[i]
            else:
                sign = 1
            dQ_i = 0.0
            for j in xrange(self.N):
                if self.C[j] == C_i and j != i:
                    dQ_i += sign * self.get_Q_ij(i, j)
                    dQ_i += sign * self.get_Q_ij(j, i)
            return dQ_i
        
        def get_Q(self):
            Q = 0.0
            for i in xrange(self.N):
                for j in xrange(self.N):
                    if self.C[j] == self.C[i]:
                        Q += self.get_Q_ij(i, j)
            return Q
        
        def group(self):
            C_map = {}
            for i, C_i in enumerate(set(self.C)):
                C_map[C_i] = i
            N = len(C_map)
            W = [None] * N
            for i in xrange(N):
                W[i] = [0.0] * N
            for self_i in xrange(self.N):
                i = C_map[self.C[self_i]]
                for self_j in xrange(self.N):
                    j = C_map[self.C[self_j]]
                    W[i][j] += self.W[self_i][self_j]
            return W
    
    @staticmethod
    def clean(W_orig):
        N = len(W_orig)
        W = [None] * N
        for i in xrange(N):
            W[i] = [0.0] * N
            for j in xrange(N):
                W_orig_ij = W_orig[i][j]
                if W_orig_ij is not None:
                    W[i][j] = abs(W_orig_ij)
        return W
    
    @staticmethod
    def calculate(W):
        state = Modularity.State(Modularity.clean(W))
        if state.N <= 1 or state.S == 0.0:
            return 0.0
        Q_prev = 0.0
        while True:
            while True:
                done = True
                for i in utility.shuffled(xrange(state.N)):
                    dQ = {}
                    dQ[state.C[i]] = 0.0
                    dQ_remove = state.get_dQ(i, None)
                    for j in state.E[i]:
                        C_j = state.C[j]
                        if C_j not in dQ:
                            dQ[C_j] = dQ_remove + state.get_dQ(i, C_j)
                    dQ_best = max(dQ.itervalues())
                    if dQ_best > 0.0:
                        C_best = [C_j for C_j, dQ_C_j in dQ.iteritems() if dQ_C_j == dQ_best]
                        state.C[i] = random.choice(C_best)
                        done = False
                if done:
                    break
            Q = state.get_Q()
            if Q - Q_prev < Modularity.dQ_min:
                return Q_prev
            state = Modularity.State(state.group())
            Q_prev = Q
    
    def __init__(self):
        raise NotImplementedError
