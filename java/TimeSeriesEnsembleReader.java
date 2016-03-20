import java.io.*;
import java.util.*;
import java.util.regex.*;

public class TimeSeriesEnsembleReader implements AutoCloseable {
    private static final Pattern agent = Pattern.compile("# AGENT (\\d+)");
    private static final Pattern dimensions = Pattern.compile("# DIMENSIONS (\\d+) (\\d+) (\\d+)");
    
    private BufferedReader reader;
    
    public TimeSeriesEnsembleReader(InputStream in) {
        reader = new BufferedReader(new InputStreamReader(in));
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
            ensemble.addTimeSeries(timeSeries);
        }
        return ensemble;
    }
    
    private String getExceptionMessage(String line) {
        return String.format("Unexpected line '%s'.", line);
    }
    
    private TimeSeriesEnsemble readHeader() throws IOException {
        int agentIndex;
        {
            String line = reader.readLine();
            if (line == null) {
                return null;
            }
            Matcher matcher = agent.matcher(line);
            if (!matcher.matches()) {
                throw new IOException(getExceptionMessage(line));
            }
            agentIndex = Integer.parseInt(matcher.group(1));
        }
        int neuronCount;
        int inputNeuronCount;
        int outputNeuronCount;
        {
            String line = reader.readLine();
            Matcher matcher = dimensions.matcher(line);
            if (!matcher.matches()) {
                throw new IOException(getExceptionMessage(line));
            }
            neuronCount = Integer.parseInt(matcher.group(1));
            inputNeuronCount = Integer.parseInt(matcher.group(2));
            outputNeuronCount = Integer.parseInt(matcher.group(3));
        }
        TimeSeriesEnsemble ensemble = new TimeSeriesEnsemble(agentIndex, neuronCount, inputNeuronCount, outputNeuronCount);
        {
            {
                String line = reader.readLine();
                if (!line.equals("# BEGIN SYNAPSES")) {
                    throw new IOException(getExceptionMessage(line));
                }
            }
            while (true) {
                String line = reader.readLine();
                if (line.equals("# END SYNAPSES")) {
                    break;
                }
                try (Scanner scanner = new Scanner(line)) {
                    int preNeuronIndex = scanner.nextInt();
                    while (scanner.hasNext()) {
                        int postNeuronIndex = scanner.nextInt();
                        ensemble.addSynapse(new Synapse(preNeuronIndex, postNeuronIndex));
                    }
                }
            }
        }
        return ensemble;
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
            double[] values = new double[dimension];
            try (Scanner scanner = new Scanner(line)) {
                for (int index = 0; index < dimension; index++) {
                    values[index] = scanner.nextDouble();
                }
                if (scanner.hasNext()) {
                    throw new IOException(getExceptionMessage(line));
                }
            }
            timeSeries.add(values);
        }
    }
    
    public void close() throws IOException {
        reader.close();
    }
}
