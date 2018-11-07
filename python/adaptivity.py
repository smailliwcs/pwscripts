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

def getPath(path, run):
    return os.path.join(path, "{0}-adaptivity.txt".format(utility.getKey(run)))

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
parser.add_argument("runs", metavar = "RUNS")
parser.add_argument("trials", metavar = "TRIALS", type = int)
parser.add_argument("agents", metavar = "AGENTS", type = int)
parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
parser.add_argument("--single", metavar = "RUN:AGENT")
parser.add_argument("--multiplier", metavar = "MULTIPLIER", type = float)
parser.add_argument("--path", metavar = "PATH", default = ".")
args = parser.parse_args()
if args.single is not None:
    assert args.trials == 1
assert not os.path.exists("run")
agents = []
for run in utility.getRuns(args.runs):
    for agent in utility.getAgents(run):
        agents.append({
            "run": run,
            "index": agent
        })
    if args.single is not None:
        continue
    with open(getPath(args.path, run), "w") as f:
        f.write("# trials = {0}\n".format(args.trials))
        f.write("# agents = {0}\n".format(args.agents))
        f.write("# stage = {0}\n".format(args.stage))
        if args.multiplier is not None:
            f.write("# multiplier = {0}\n".format(args.multiplier))
batchCount = int(math.ceil(float(len(agents)) / args.agents))
for trialIndex in xrange(args.trials):
    random.shuffle(agents)
    batches = [None] * batchCount
    start = 0
    for batchIndex in xrange(batchCount):
        end = int(math.floor((batchIndex + 1) * float(len(agents)) / batchCount))
        batches[batchIndex] = agents[start:end]
        start = end
    if args.single is not None:
        chunks = args.single.rsplit(":", 1)
        batches[0][0] = {
            "run": chunks[0],
            "index": int(chunks[1])
        }
    for batch in batches:
        missing = []
        with open("genomeSeeds.txt", "w") as g, open("synapseSeeds.txt", "w") as s:
            for agent in batch:
                genome = os.path.join(agent["run"], "genome", "agents", "genome_{0}.txt.gz".format(agent["index"]))
                synapses = os.path.join(agent["run"], "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent["index"], args.stage))
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
            "--RecordBrainFunction {0}".format(args.single is not None),
            "--RecordCarry False",
            "--RecordCollisions False",
            "--RecordComplexity False",
            "--RecordContacts True",
            "--RecordEnergy False",
            "--RecordFoodConsumption True",
            "--RecordFoodEnergy False",
            "--RecordGeneStats False",
            "--RecordGenomes {0}".format(args.single is not None),
            "--RecordGitRevision False",
            "--RecordPopulation False",
            "--RecordPosition False",
            "--RecordSeparations False",
            "--RecordSynapses {0}".format(args.single is not None)
        ]
        if args.multiplier is not None:
            pwargs.append("--AgeEnergyMultiplier {0}".format(args.multiplier))
        pwargs.append("\"{0}\"".format(args.worldfile))
        os.system("./Polyworld {0}".format(" ".join(pwargs)))
        if args.single is not None:
            break
        wait(lambda: os.path.exists(os.path.join("run", "endStep.txt")))
        survival = getSurvival()
        foraging = getForaging()
        reproductive = getReproductive()
        for run in utility.getRuns(args.runs):
            with open(getPath(args.path, run), "a") as f:
                for index in utility.getAgents("run"):
                    agent = batch[index - 1]
                    if agent["run"] == run:
                        f.write("{0} {1} {2} {3}\n".format(agent["index"], survival[index], foraging[index], reproductive[index]))
        shutil.rmtree("run")
        wait(lambda: not os.path.exists("run"))
os.remove("genomeSeeds.txt")
os.remove("synapseSeeds.txt")
