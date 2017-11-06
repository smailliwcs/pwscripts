import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kozachenko.*;

public class Entropy {
    private static EntropyCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new EntropyCalculatorMultiVariateKozachenko();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), getEntropy(ensemble));
            }
        }
    }
    
    private static double getEntropy(TimeSeriesEnsemble ensemble) throws Exception {
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        calculator.initialise(neuronIndices.length);
        calculator.setObservations(ensemble.combine().getColumns(neuronIndices));
        return calculator.computeAverageLocalOfObservations();
    }
}
