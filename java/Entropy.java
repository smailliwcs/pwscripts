import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kernel.*;

public class Entropy {
    private static EntropyCalculator calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new EntropyCalculatorKernel();
        Utility.setProperties(calculator, System.out);
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
    
    private static double calculate(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
        calculator.initialise();
        calculator.setObservations(ensemble.getCombinedTimeSeries().get(neuronIndex));
        return calculator.computeAverageLocalOfObservations();
    }
}
