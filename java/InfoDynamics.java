public class InfoDynamics {
    private static String metric;
    private static int embeddingLength;
    private static TransferEntropyCalculator calculator;
    
    public static void main(String[] args) throws Exception {
        parseArgs(args);
        System.out.printf("# k = %d%n", embeddingLength);
        calculator = new TransferEntropyCalculator(embeddingLength);
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
        if (args.length != 2) {
            throw new IllegalArgumentException();
        }
        metric = args[0];
        embeddingLength = Integer.parseInt(args[1]);
        if (embeddingLength < 1) {
            throw new IllegalArgumentException();
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
