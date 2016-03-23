import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import java.util.*;

public class ActiveInfoStorage {
    private static ActiveInfoStorageCalculator calculator;
    private static Properties properties;
    
    public static void main(String[] args) throws Exception {
        calculator = new ActiveInfoStorageCalculatorKraskov();
        properties = Utility.setProperties(calculator);
        Utility.printProperties(properties, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
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
