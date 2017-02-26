import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoStorage {
    private static int embedding;
    private static MutualInfoCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s EMBEDDING%n", InfoStorage.class.getSimpleName());
            return;
        }
        calculator = new MutualInfoCalculatorMultiVariateKraskov1();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculate(ensemble));
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 1;
            embedding = Integer.parseInt(args[0]);
            assert embedding > 0;
            return true;
        } catch (Exception ex) {
            return false;
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble) throws Exception {
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        calculator.initialise(embedding * neuronIndices.length, neuronIndices.length);
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] data = timeSeries.getColumns(neuronIndices);
            calculator.addObservations(
                MatrixUtils.makeDelayEmbeddingVector(data, embedding, embedding - 1, data.length - embedding),
                MatrixUtils.selectRows(data, embedding, data.length - embedding));
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
