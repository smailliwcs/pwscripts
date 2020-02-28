# pwscripts

Scripts supporting the design, execution, and analysis of Polyworld simulations

## Prerequisites

-   [Polyworld](https://github.com/smailliwcs/polyworld)
-   Java 8 with Ant
-   Python 3 with NumPy and pandas

## Installation

1.  Clone the repository:

        $ git clone https://github.com/smailliwcs/pwscripts.git

2.  Initialize and update submodules:

        pwscripts$ git submodule init
        pwscripts$ git submodule update

3.  Build the [JIDT](https://github.com/jlizier/jidt) submodule:

        pwscripts/java/lib/jidt$ ant

4.  Build the Java code:

        pwscripts/java$ ant

5.  Configure environment variables:

    -   `PATH`: Add `pwscripts/shell`.
    -   `CLASSPATH`: Add `pwscripts/java/lib/jidt/infodynamics.jar` and `pwscripts/java/bin`.
    -   `PYTHONPATH`: Add `polyworld/scripts`.

## Usage

### Replacing Polyworld's default (rotating oblique) view with a static overhead view

    polyworld$ ln -s ../pwscripts/config/static.mf gui.mf

### Running a "legacy" simulation

    polyworld$ ./Polyworld ../pwscripts/config/legacy.wf

### Running a "modern" simulation

    polyworld$ ./Polyworld $(../pwscripts/config/modern)

To grow "poisonous" food items, pass the `-D poison` option to `modern`.

### Running driven simulations

    polyworld$ pwdriven ../pwscripts/config/legacy.wf 10 runs/driven

To ensure simulations run to completion, pass the `--complete` option to `pwdriven`.
This discards simulations that terminate prematurely (e.g., due to a population crash).

### Running passive simulations

    polyworld$ pwpassive runs/passive runs/driven

### Encoding a Polyworld "movie" in another video format (requires FFmpeg)

The entire simulation:

    polyworld$ pmvencode run/movie.pmv run/movie.mp4 640 480

A segment of the simulation:

    polyworld$ pmvencode run/movie.pmv run/movie.mp4 640 480 -- -s 9001 -e 10000

### Calculating genetic diversity

Post hoc:

    polyworld$ ./bin/genetics runs/legacy | java Diversity 0 > diversity.txt

On the fly:

    polyworld$ mkfifo genetics
    polyworld$ java Diversity 0 < genetics > diversity.txt &
    polyworld$ ./Polyworld ../pwscripts/config/legacy.wf --PopulationGeneticsLog '{ On True; }'
    polyworld$ rm genetics

### Calculating information-theoretic metrics

Post hoc:

    polyworld$ ./bin/timeseries runs/legacy death 1 10 1000 | java Complexity > complexity.txt

On the fly:

    polyworld$ mkfifo timeseries
    polyworld$ java Complexity < timeseries > complexity.txt &
    polyworld$ ./Polyworld ../pwscripts/config/legacy.wf --TimeSeriesLog '{ On True; }'
    polyworld$ rm timeseries

Other metrics include `Entropy`, `CompleteTransferEntropy`, `CollectiveTransferEntropy`, and `InfoDynamics` (which calculates the following metrics in one pass: active information storage, apparent transfer entropy, and separable information).
In general, multiple and/or longer time series may be required to achieve numerical stability.
To accomplish this when calculating post hoc, increase the first and/or last numeric arguments to `timeseries`.
When calculating on the fly, specify the `Repeats` and/or `Steps` subparameters of `TimeSeriesLog`.
For some metrics, additional arguments to `java` are required.

### Calculating other metrics

Refer to the Python code's inline documentation:

    pwscripts/python$ python calculate.py --help
