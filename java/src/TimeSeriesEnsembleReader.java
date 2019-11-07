import java.io.*;
import java.util.*;
import java.util.regex.*;

public class TimeSeriesEnsembleReader extends BufferedReader {
    private static final Pattern AGENT_PATTERN = Pattern.compile("^# AGENT (\\d+$)");
    private static final Pattern DIMENSIONS_PATTERN = Pattern.compile("^# DIMENSIONS (\\d+) (\\d+) (\\d+)$");

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
        int agentIndex = readAgentIndex();
        if (agentIndex == -1) {
            return null;
        }
        Brain brain = readBrain();
        TimeSeriesEnsemble ensemble = new TimeSeriesEnsemble(agentIndex, brain);
        while (true) {
            TimeSeries observations = readTimeSeries(brain.getNeuronCount());
            if (observations == null) {
                break;
            }
            ensemble.add(observations);
        }
        return ensemble;
    }

    private int readAgentIndex() throws IOException {
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
                int neuronCount = scanner.nextInt();
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
                int preNeuronIndex = scanner.nextInt();
                while (scanner.hasNext()) {
                    int postNeuronIndex = scanner.nextInt();
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
            List<Double> observation = new ArrayList<Double>(dimension);
            try (Scanner scanner = new Scanner(line)) {
                while (scanner.hasNext()) {
                    observation.add(scanner.nextDouble());
                }
            }
            observations.add(observation);
        }
    }
}
