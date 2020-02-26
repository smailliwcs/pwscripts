import os


def events(run):
    return os.path.join(run, "BirthsDeaths.log")


def end_time(run):
    return os.path.join(run, "endStep.txt")


def lifespans(run):
    return os.path.join(run, "lifespans.txt")


def synapses(run, agent, stage):
    return os.path.join(run, "brain", "synapses", f"synapses_{agent}_{stage.value}.txt")
