import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class TimeSeriesEnsembleReader extends BufferedReader {
    private static final Pattern AGENT_PATTERN = Pattern.compile("^# AGENT (\\d+$)");
    private static final Pattern DIMENSIONS_PATTERN = Pattern.compile("^# DIMENSIONS (\\d+) (\\d+) (\\d+)$");
    private static final Pattern SPACE_PATTERN = Pattern.compile(" ");

    public TimeSeriesEnsembleReader(Reader in) {
        super(in);
    }

    public void readArguments(PrintStream out) throws IOException {
        String line = readLine();
        assert line.equals("# BEGIN ARGUMENTS");
        while (true) {
            line = readLine();
            if (line.equals("# END ARGUMENTS")) {
                break;
            }
            out.printf("# %s%n", line);
        }
    }

    public TimeSeriesEnsemble readTimeSeriesEnsemble() throws IOException {
        int agentId = readAgentId();
        if (agentId == -1) {
            return null;
        }
        Brain brain = readBrain();
        TimeSeriesEnsemble ensemble = new TimeSeriesEnsemble(agentId, brain);
        while (true) {
            TimeSeries observations = readTimeSeries(brain.getNeuronCount());
            if (observations == null) {
                break;
            }
            ensemble.add(observations);
        }
        return ensemble;
    }

    private int readAgentId() throws IOException {
        String line = readLine();
        if (line == null) {
            return -1;
        }
        Matcher matcher = AGENT_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        return Integer.parseInt(matcher.group(1));
    }

    private Brain readBrain() throws IOException {
        String line = readLine();
        Matcher matcher = DIMENSIONS_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        int neuronCount = Integer.parseInt(matcher.group(1));
        int inputNeuronCount = Integer.parseInt(matcher.group(2));
        int outputNeuronCount = Integer.parseInt(matcher.group(3));
        Brain brain = new Brain(neuronCount, inputNeuronCount, outputNeuronCount);
        for (Nerve nerve : readNerves()) {
            brain.addNerve(nerve);
        }
        for (Synapse synapse : readSynapses()) {
            brain.addSynapse(synapse);
        }
        return brain;
    }

    private Collection<Nerve> readNerves() throws IOException {
        String line = readLine();
        assert line.equals("# BEGIN NERVES");
        int neuronStartIndex = 0;
        Collection<Nerve> nerves = new LinkedList<Nerve>();
        while (true) {
            line = readLine();
            if (line.equals("# END NERVES")) {
                break;
            }
            try (Scanner scanner = new Scanner(line)) {
                String name = scanner.next();
                int neuronCount = Integer.parseInt(scanner.next());
                nerves.add(new Nerve(name, neuronStartIndex, neuronCount));
                neuronStartIndex += neuronCount;
            }
        }
        return nerves;
    }

    private Collection<Synapse> readSynapses() throws IOException {
        String line = readLine();
        assert line.equals("# BEGIN SYNAPSES");
        Collection<Synapse> synapses = new LinkedList<Synapse>();
        while (true) {
            line = readLine();
            if (line.equals("# END SYNAPSES")) {
                break;
            }
            try (Scanner scanner = new Scanner(line)) {
                int preNeuronIndex = Integer.parseInt(scanner.next());
                while (scanner.hasNext()) {
                    int postNeuronIndex = Integer.parseInt(scanner.next());
                    synapses.add(new Synapse(preNeuronIndex, postNeuronIndex));
                }
            }
        }
        return synapses;
    }

    private TimeSeries readTimeSeries(int dimension) throws IOException {
        String line = readLine();
        if (line.equals("# BEGIN ENSEMBLE")) {
            line = readLine();
        }
        if (line.equals("# END ENSEMBLE")) {
            return null;
        }
        assert line.equals("# BEGIN TIME SERIES");
        TimeSeries observations = new TimeSeries(dimension);
        while (true) {
            line = readLine();
            if (line.equals("# END TIME SERIES")) {
                return observations;
            }
            List<Double> observation = SPACE_PATTERN.splitAsStream(line)
                    .map(chunk -> Double.valueOf(chunk))
                    .collect(Collectors.toCollection(ArrayList::new));
            observations.add(observation);
        }
    }
}
