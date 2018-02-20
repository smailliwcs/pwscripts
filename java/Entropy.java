import infodynamics.measures.discrete.*;
import infodynamics.utils.*;

public class Entropy {
    private static int base;
    private static EntropyCalculatorDiscrete calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s BASE%n", Entropy.class.getSimpleName());
            return;
        }
        calculator = new EntropyCalculatorDiscrete(base);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# base = %d%n", base);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                int[] neuronIndices = ensemble.getProcessingNeuronIndices();
                double[] entropies = new double[neuronIndices.length];
                for (int index = 0; index < neuronIndices.length; index++) {
                    entropies[index] = getEntropy(ensemble, neuronIndices[index]);
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), MatrixUtils.mean(entropies));
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 1;
            base = Integer.parseInt(args[0]);
            assert base > 1;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static double getEntropy(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
        calculator.initialise();
        for (TimeSeries timeSeries : ensemble) {
            calculator.addObservations(timeSeries.getColumnDiscrete(neuronIndex, base));
        }
        return calculator.computeAverageLocalOfObservations();
    }
}
