import java.io.*;
import java.util.*;
import java.util.regex.*;

public class TimeSeriesEnsembleReader implements AutoCloseable {
    private static final Pattern ARGUMENT = Pattern.compile("[a-zA-Z0-9_\\-]+ = .+");
    private static final Pattern AGENT = Pattern.compile("# AGENT (?<agentIndex>\\d+)");
    private static final Pattern DIMENSIONS = Pattern.compile("# DIMENSIONS (?<neuronCount>\\d+) (?<inputNeuronCount>\\d+) (?<outputNeuronCount>\\d+)");
    
    private static String getExceptionMessage(String line) {
        return String.format("Unexpected line '%s'.", line);
    }
    
    private BufferedReader reader;
    
    public TimeSeriesEnsembleReader(InputStream in) {
        reader = new BufferedReader(new InputStreamReader(in));
    }
    
    public void readArguments(PrintStream out) throws IOException {
        {
            String line = reader.readLine();
            if (!line.equals("# BEGIN ARGUMENTS")) {
                throw new IOException(getExceptionMessage(line));
            }
        }
        while (true) {
            String line = reader.readLine();
            if (line.equals("# END ARGUMENTS")) {
                break;
            }
            Matcher matcher = ARGUMENT.matcher(line);
            if (!matcher.matches()) {
                throw new IOException(getExceptionMessage(line));
            }
            out.printf("# %s%n", line);
        }
    }
    
    public TimeSeriesEnsemble read() throws IOException {
        TimeSeriesEnsemble ensemble = readHeader();
        if (ensemble == null) {
            return null;
        }
        while (true) {
            TimeSeries timeSeries = readTimeSeries(ensemble.getNeuronCount());
            if (timeSeries == null) {
                break;
            }
            ensemble.add(timeSeries);
        }
        return ensemble;
    }
    
    private TimeSeriesEnsemble readHeader() throws IOException {
        int agentIndex;
        {
            String line = reader.readLine();
            if (line == null) {
                return null;
            }
            Matcher matcher = AGENT.matcher(line);
            if (!matcher.matches()) {
                throw new IOException(getExceptionMessage(line));
            }
            agentIndex = Integer.parseInt(matcher.group("agentIndex"));
        }
        int neuronCount;
        int inputNeuronCount;
        int outputNeuronCount;
        {
            String line = reader.readLine();
            Matcher matcher = DIMENSIONS.matcher(line);
            if (!matcher.matches()) {
                throw new IOException(getExceptionMessage(line));
            }
            neuronCount = Integer.parseInt(matcher.group("neuronCount"));
            inputNeuronCount = Integer.parseInt(matcher.group("inputNeuronCount"));
            outputNeuronCount = Integer.parseInt(matcher.group("outputNeuronCount"));
        }
        return new TimeSeriesEnsemble(agentIndex, neuronCount, inputNeuronCount, outputNeuronCount);
    }
    
    private TimeSeries readTimeSeries(int dimension) throws IOException {
        {
            String line = reader.readLine();
            if (line.equals("# BEGIN ENSEMBLE")) {
                line = reader.readLine();
            }
            if (line.equals("# END ENSEMBLE")) {
                return null;
            }
            if (!line.equals("# BEGIN TIME SERIES")) {
                throw new IOException(getExceptionMessage(line));
            }
        }
        TimeSeries timeSeries = new TimeSeries(dimension);
        while (true) {
            String line = reader.readLine();
            if (line.equals("# END TIME SERIES")) {
                return timeSeries;
            }
            double[] row = new double[dimension];
            try (Scanner scanner = new Scanner(line)) {
                for (int index = 0; index < dimension; index++) {
                    row[index] = scanner.nextDouble();
                }
                if (scanner.hasNext()) {
                    throw new IOException(getExceptionMessage(line));
                }
            }
            timeSeries.add(row);
        }
    }
    
    public void close() throws IOException {
        reader.close();
    }
}
