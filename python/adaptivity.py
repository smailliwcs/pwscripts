import argparse
import collections
import math
import os
import random
import shutil
import sys
import time
import utility

def wait(predicate, delay = 1.0, attempts = 10):
    attempt = 0
    while True:
        if predicate():
            return True
        attempt += 1
        if attempt == attempts:
            return False
        time.sleep(delay)

def getSurvival():
    values = {}
    path = os.path.join("run", "lifespans.txt")
    for row in utility.getDataTable(path, "LifeSpans").rows():
        values[row["Agent"]] = row["DeathStep"] - row["BirthStep"]
    return values

def getForaging():
    values = collections.defaultdict(float)
    path = os.path.join("run", "energy", "consumption.txt")
    for row in utility.getDataTable(path, "FoodConsumption").rows():
        values[row["Agent"]] += row["Energy"]
    return values

def getReproductive():
    values = collections.defaultdict(int)
    path = os.path.join("run", "events", "contacts.log")
    for row in utility.getDataTable(path, "Contacts").rows():
        if "M" in row["Events"] and "o" in row["Events"]:
            values[row["Agent1"]] += 1
            values[row["Agent2"]] += 1
    return values

parser = argparse.ArgumentParser()
parser.add_argument("worldfile", metavar = "WORLDFILE")
parser.add_argument("run", metavar = "RUN")
parser.add_argument("trials", metavar = "TRIALS", type = int)
parser.add_argument("agents", metavar = "AGENTS", type = int)
parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
parser.add_argument("output", metavar = "OUTPUT")
parser.add_argument("--multiplier", metavar = "MULTIPLIER", type = float)
args = parser.parse_args()
assert not os.path.exists("run")
agents = list(utility.getAgents(args.run))
batchCount = int(math.ceil(float(len(agents)) / args.agents))
with open(args.output, "w") as f:
    f.write("# trials = {0}\n".format(args.trials))
    f.write("# agents = {0}\n".format(args.agents))
    f.write("# stage = {0}\n".format(args.stage))
    if args.multiplier is not None:
        f.write("# multiplier = {0}\n".format(args.multiplier))
for trialIndex in xrange(args.trials):
    random.shuffle(agents)
    batches = [None] * batchCount
    start = 0
    for batchIndex in xrange(batchCount):
        end = int(math.floor((batchIndex + 1) * float(len(agents)) / batchCount))
        batches[batchIndex] = agents[start:end]
        start = end
    for batch in batches:
        missing = []
        with open("genomeSeeds.txt", "w") as g, open("synapseSeeds.txt", "w") as s:
            for agent in batch:
                genome = os.path.join(args.run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
                synapses = os.path.join(args.run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, args.stage))
                if not os.path.exists(synapses):
                    sys.stderr.write("Missing synapses file {0}\n".format(synapses))
                    missing.append(agent)
                    continue
                g.write("{0}\n".format(genome))
                s.write("{0}\n".format(synapses))
        for agent in missing:
            batch.remove(agent)
        pwargs = [
            "--AdaptivityMode True",
            "--InitSeed $(date +%s)",
            "--InitAgents {0}".format(len(batch)),
            "--SeedGenomeFromRun True",
            "--SeedSynapsesFromRun True",
            "--FreezeSeededSynapses True",
            "--RecordAdamiComplexity False",
            "--RecordAgentEnergy False",
            "--RecordBarrierPosition False",
            "--RecordBirthsDeaths False",
            "--RecordBrainAnatomy False",
            "--RecordBrainFunction False",
            "--RecordCarry False",
            "--RecordCollisions False",
            "--RecordComplexity False",
            "--RecordContacts True",
            "--RecordEnergy False",
            "--RecordFoodConsumption True",
            "--RecordFoodEnergy False",
            "--RecordGeneStats False",
            "--RecordGenomes False",
            "--RecordGitRevision False",
            "--RecordPopulation False",
            "--RecordPosition False",
            "--RecordSeparations False",
            "--RecordSynapses False"
        ]
        if args.multiplier is not None:
            pwargs.append("--AgeEnergyMultiplier {0}".format(args.multiplier))
        pwargs.append("\"{0}\"".format(args.worldfile))
        os.system("./Polyworld {0}".format(" ".join(pwargs)))
        wait(lambda: os.path.exists(os.path.join("run", "endStep.txt")))
        survival = getSurvival()
        foraging = getForaging()
        reproductive = getReproductive()
        with open(args.output, "a") as f:
            for agent in xrange(1, len(batch) + 1):
                f.write("{0} {1} {2} {3}\n".format(batch[agent - 1], survival[agent], foraging[agent], reproductive[agent]))
        shutil.rmtree("run")
        wait(lambda: not os.path.exists("run"))
os.remove("genomeSeeds.txt")
os.remove("synapseSeeds.txt")
