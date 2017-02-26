import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;

public class InfoTransfer {
    private static int sourceEmbedding;
    private static int targetEmbedding;
    private static ConditionalTransferEntropyCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s SOURCE_EMBEDDING TARGET_EMBEDDING%n", InfoTransfer.class.getSimpleName());
            return;
        }
        ConditionalMutualInfoCalculatorMultiVariate mutualInfoCalculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        calculator = new ConditionalTransferEntropyCalculatorMultiVariate(mutualInfoCalculator, sourceEmbedding, targetEmbedding);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# sourceEmbedding = %d%n", sourceEmbedding);
            System.out.printf("# targetEmbedding = %d%n", targetEmbedding);
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
            assert args.length == 2;
            sourceEmbedding = Integer.parseInt(args[0]);
            assert sourceEmbedding > 0;
            targetEmbedding = Integer.parseInt(args[1]);
            assert targetEmbedding > 0;
            return true;
        } catch (Exception ex) {
            return false;
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble) throws Exception {
        int[] inputNeuronIndices = ensemble.getInputNeuronIndices();
        int[] outputNeuronIndices = ensemble.getOutputNeuronIndices();
        calculator.initialise(inputNeuronIndices.length, outputNeuronIndices.length);
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] source = timeSeries.getColumns(inputNeuronIndices);
            double[][] target = timeSeries.getColumns(outputNeuronIndices);
            calculator.addObservations(source, target);
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
