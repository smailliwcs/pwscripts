import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;

public class ActiveInfoStorage {
    private static ActiveInfoStorageCalculator calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new ActiveInfoStorageCalculatorKraskov();
        Utility.setProperties(calculator, System.out);
        parseArgs(args);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                for (int neuronIndex : ensemble.getProcessingNeuronIndices()) {
                    System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), neuronIndex, calculate(ensemble, neuronIndex));
                }
            }
        }
    }
    
    private static void parseArgs(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException();
        }
        calculator.setProperty(calculator.K_PROP_NAME, args[0]);
        System.out.printf("# %s = %s%n", calculator.K_PROP_NAME, args[0]);
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
        calculator.initialise();
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            calculator.addObservations(timeSeries.get(neuronIndex));
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
