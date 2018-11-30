import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;
import java.util.*;

public class InfoTransferCollective {
    private static boolean gpu;
    private static int embedding;
    private static ConditionalMutualInfoCalculatorMultiVariateKraskov1 calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s GPU EMBEDDING%n", InfoTransferCollective.class.getSimpleName());
            return;
        }
        calculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        if (gpu) {
            calculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, Boolean.TRUE.toString());
        }
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double sum = 0.0;
                int count = 0;
                for (int neuronIndex : ensemble.getProcessingNeuronIndices()) {
                    sum += getTransfer(ensemble, neuronIndex);
                    count++;
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), count, sum);
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 2;
            int index = 0;
            gpu = Boolean.parseBoolean(args[index++]);
            embedding = Integer.parseInt(args[index++]);
            assert embedding > 0;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble, int postNeuronIndex) throws Exception {
        int[] preNeuronIndices = ensemble.getPreNeuronIndices(postNeuronIndex);
        calculator.initialise(preNeuronIndices.length, 1, embedding);
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            int length = timeSeries.size() - embedding;
            double[][] source = timeSeries.getColumns(preNeuronIndices);
            double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
            calculator.addObservations(
                MatrixUtils.selectRows(source, embedding - 1, length),
                MatrixUtils.selectRows(target, embedding, length),
                MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, length));
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
