import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class TimeSeriesEnsembleReader extends BufferedReader {
    private static final Pattern AGENT_PATTERN = Pattern.compile("^# AGENT (\\d+)$");
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
        readNerves(brain);
        readSynapses(brain);
        return brain;
    }

    private void readNerves(Brain brain) throws IOException {
        String line = readLine();
        assert line.equals("# BEGIN NERVES");
        int neuronStartIndex = 0;
        while (true) {
            line = readLine();
            if (line.equals("# END NERVES")) {
                break;
            }
            String[] chunks = SPACE_PATTERN.split(line);
            String name = chunks[0];
            int neuronCount = Integer.parseInt(chunks[1]);
            brain.addNerve(new Nerve(name, neuronStartIndex, neuronCount));
            neuronStartIndex += neuronCount;
        }
    }

    private void readSynapses(Brain brain) throws IOException {
        String line = readLine();
        assert line.equals("# BEGIN SYNAPSES");
        while (true) {
            line = readLine();
            if (line.equals("# END SYNAPSES")) {
                break;
            }
            String[] chunks = SPACE_PATTERN.split(line);
            int preNeuronIndex = Integer.parseInt(chunks[0]);
            for (int chunkIndex = 1; chunkIndex < chunks.length; chunkIndex++) {
                int postNeuronIndex = Integer.parseInt(chunks[chunkIndex]);
                brain.addSynapse(new Synapse(preNeuronIndex, postNeuronIndex));
            }
        }
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
            observations.add(SPACE_PATTERN.splitAsStream(line)
                    .map(Double::valueOf)
                    .collect(Collectors.toCollection(ArrayList::new)));
        }
    }
}
