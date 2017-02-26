import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;

public class InfoModification {
    private static int sourceEmbedding;
    private static int targetEmbedding;
    private static int conditionalEmbedding;
    private static ConditionalTransferEntropyCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s SOURCE_EMBEDDING TARGET_EMBEDDING CONDITIONAL_EMBEDDING%n", InfoTransfer.class.getSimpleName());
            return;
        }
        ConditionalMutualInfoCalculatorMultiVariate mutualInfoCalculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        calculator = new ConditionalTransferEntropyCalculatorMultiVariate(mutualInfoCalculator, sourceEmbedding, targetEmbedding, conditionalEmbedding);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# sourceEmbedding = %d%n", sourceEmbedding);
            System.out.printf("# targetEmbedding = %d%n", targetEmbedding);
            System.out.printf("# conditionalEmbedding = %d%n", conditionalEmbedding);
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
            assert args.length == 3;
            sourceEmbedding = Integer.parseInt(args[0]);
            assert sourceEmbedding > 0;
            targetEmbedding = Integer.parseInt(args[1]);
            assert targetEmbedding > 0;
            conditionalEmbedding = Integer.parseInt(args[2]);
            assert conditionalEmbedding > 0;
            return true;
        } catch (Exception ex) {
            return false;
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble) throws Exception {
        int[] internalNeuronIndices = ensemble.getInternalNeuronIndices();
        int[] outputNeuronIndices = ensemble.getOutputNeuronIndices();
        int[] inputNeuronIndices = ensemble.getInputNeuronIndices();
        if (internalNeuronIndices.length == 0) {
            return 0.0;
        } else {
            calculator.initialise(internalNeuronIndices.length, outputNeuronIndices.length, inputNeuronIndices.length);
            calculator.startAddObservations();
            for (TimeSeries timeSeries : ensemble) {
                double[][] source = timeSeries.getColumns(internalNeuronIndices);
                double[][] target = timeSeries.getColumns(outputNeuronIndices);
                double[][] conditional = timeSeries.getColumns(inputNeuronIndices);
                calculator.addObservations(source, target, conditional);
            }
            calculator.finaliseAddObservations();
            return calculator.computeAverageLocalOfObservations();
        }
    }
}
