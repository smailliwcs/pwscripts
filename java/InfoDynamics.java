public class InfoDynamics {
    private static String metric;
    private static int sourceEmbedding;
    private static int targetEmbedding;
    private static int conditionalEmbedding;
    private static ConditionalTransferEntropyCalculatorMultiVariate calculator;
    
    public static void main(String[] args) throws Exception {
        parseArgs(args);
        calculator = new ConditionalTransferEntropyCalculatorMultiVariate(sourceEmbedding, targetEmbedding, conditionalEmbedding);
        Utility.setProperties(calculator, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculate(ensemble));
            }
        }
    }
    
    private static void parseArgs(String[] args) {
        if (args.length < 3 || args.length > 4) {
            throw new IllegalArgumentException();
        }
        metric = args[0];
        sourceEmbedding = Integer.parseInt(args[1]);
        if (sourceEmbedding < 1) {
            throw new IllegalArgumentException();
        }
        System.out.printf("# l_HISTORY = %d%n", sourceEmbedding);
        targetEmbedding = Integer.parseInt(args[2]);
        if (targetEmbedding < 0) {
            throw new IllegalArgumentException();
        }
        System.out.printf("# k_HISTORY = %d%n", targetEmbedding);
        if (args.length >= 4) {
            conditionalEmbedding = Integer.parseInt(args[3]);
            if (conditionalEmbedding < 0) {
                throw new IllegalArgumentException();
            }
            System.out.printf("# COND_EMBED_LENGTHS = %d%n", conditionalEmbedding);
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble) throws Exception {
        switch (metric) {
            case "storage":
                return calculator.calculate(ensemble, ensemble.getInputNeuronIndices(), ensemble.getInternalNeuronIndices());
            case "transfer":
                return calculator.calculate(ensemble, ensemble.getInputNeuronIndices(), ensemble.getOutputNeuronIndices());
            case "modification":
                return calculator.calculate(ensemble, ensemble.getInternalNeuronIndices(), ensemble.getOutputNeuronIndices(), ensemble.getInputNeuronIndices());
            default:
                throw new IllegalArgumentException();
        }
    }
}
