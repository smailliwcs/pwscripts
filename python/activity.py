import argparse
import collections
import gzip
import os
import random
import sys
import utility

class Gene(object):
    def __init__(self, value, timestep, usage = 0):
        self.value = value
        self.timestep = timestep
        self.usage = usage
    
    def getActivity(self, timestep):
        return timestep - self.timestep

def getGenome(run, agent):
    path = os.path.join(run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
    with gzip.open(path) as f:
        for line in f:
            yield int(line)

def getFile(run, name):
    path = os.path.join(run, "data")
    utility.makeDirectories(path)
    fn = gzip.open if name.endswith(".gz") else open
    return fn(os.path.join(path, name), "w")

parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
args = parser.parse_args()
genome = []
geneLists = []
usage = utility.getInitialAgentCount(args.run)
for value in getGenome(args.run, 1):
    gene = Gene(value, 0, usage)
    genome.append(gene)
    geneLists.append([gene])
genomes = {}
for agent in xrange(1, utility.getInitialAgentCount(args.run) + 1):
    genomes[agent] = genome
events = collections.defaultdict(list)
for event in utility.Event.read(args.run):
    events[event.timestep].append(event)
with getFile(args.run, "diversity.txt") as d, getFile(args.run, "activity.txt.gz") as a:
    for timestep in xrange(utility.getFinalTimestep(args.run) + 1):
        if timestep % 100 == 0:
            sys.stderr.write("{0}\n".format(timestep))
        for event in events[timestep]:
            if event.eventType == utility.EventType.BIRTH:
                genome1 = genomes[event.parent1]
                genome2 = genomes[event.parent2]
                genome = []
                for index, value in enumerate(getGenome(args.run, event.agent)):
                    gene1 = genome1[index]
                    gene2 = genome2[index]
                    if gene1.value == value:
                        if gene2.value == value:
                            gene = random.choice((gene1, gene2))
                        else:
                            gene = gene1
                    elif gene2.value == value:
                        gene = gene2
                    else:
                        gene = Gene(value, event.timestep)
                        geneLists[index].append(gene)
                    gene.usage += 1
                    genome.append(gene)
                genomes[event.agent] = genome
            elif event.eventType == utility.EventType.DEATH:
                for index, gene in enumerate(genomes[event.agent]):
                    gene.usage -= 1
                    if gene.usage == 0:
                        geneLists[index].remove(gene)
                del genomes[event.agent]
        diversity = 0
        activities = collections.defaultdict(int)
        for geneList in geneLists:
            diversity += len(geneList)
            for gene in geneList:
                activities[gene.getActivity(timestep)] += 1
        d.write("{0} {1}\n".format(timestep, diversity))
        for activity, count in activities.iteritems():
            a.write("{0} {1} {2}\n".format(timestep, activity, count))
