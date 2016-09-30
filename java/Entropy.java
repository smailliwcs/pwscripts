import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kernel.*;
import infodynamics.utils.*;
import java.util.*;

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
                int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculate(ensemble, processingNeuronIndices));
            }
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble, int[] neuronIndices) throws Exception {
        TimeSeries timeSeries = ensemble.getCombinedTimeSeries();
        double[] values = new double[neuronIndices.length];
        for (int valueIndex = 0; valueIndex < neuronIndices.length; valueIndex++) {
            calculator.initialise();
            calculator.setObservations(timeSeries.get(neuronIndices[valueIndex]));
            values[valueIndex] = calculator.computeAverageLocalOfObservations();
        }
        return MatrixUtils.mean(values);
    }
}
