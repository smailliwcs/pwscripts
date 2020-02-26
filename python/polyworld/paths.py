import os


def events(run):
    return os.path.join(run, "BirthsDeaths.log")


def end_time(run):
    return os.path.join(run, "endStep.txt")


def food_consumption(run):
    return os.path.join(run, "energy", "consumption.txt")


def food_energy(run):
    return os.path.join(run, "energy", "food.txt")


def gene_indices(run):
    return os.path.join(run, "genome", "meta", "geneindex.txt")


def genome(run, agent):
    return os.path.join(run, "genome", "agents", f"genome_{agent}.txt")


def lifespans(run):
    return os.path.join(run, "lifespans.txt")


def population(run):
    return os.path.join(run, "population.txt")


def synapses(run, agent, stage):
    return os.path.join(run, "brain", "synapses", f"synapses_{agent}_{stage.value}.txt")
