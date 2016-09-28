import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kozachenko.*;
import java.util.*;

public class Entropy {
    private static EntropyCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new EntropyCalculatorMultiVariateKozachenko();
        Utility.setProperties(calculator, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculate(ensemble, processingNeuronIndices));
            }
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble, int[] neuronIndices) throws Exception {
        calculator.initialise(neuronIndices.length);
        calculator.setObservations(ensemble.getCombinedTimeSeries().get(neuronIndices));
        return calculator.computeAverageLocalOfObservations();
    }
}
