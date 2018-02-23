import infodynamics.measures.continuous.kozachenko.*;
import infodynamics.utils.*;

public class Entropy {
    private static EntropyCalculatorMultiVariateKozachenko calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new EntropyCalculatorMultiVariateKozachenko();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double sum = 0.0;
                int count = 0;
                for (int neuronIndex : ensemble.getProcessingNeuronIndices()) {
                    sum += getEntropy(ensemble, neuronIndex);
                    count++;
                }
                double entropy = sum / count;
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), entropy);
            }
        }
    }
    
    private static double getEntropy(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
        calculator.initialise(1);
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            calculator.addObservations(timeSeries.getColumns(new int[] { neuronIndex }));
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
