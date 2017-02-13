import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoDynamics {
    private static String metric;
    private static int sourceEmbedding;
    private static int targetEmbedding;
    private static int conditionalEmbedding;
    
    public static void main(String[] args) throws Exception {
        parseArgs(args);
        if (metric.equals("storage")) {
            calculateStorage();
        } else if (metric.equals("transfer") || metric.equals("modification")) {
            calculateTransferOrModification();
        } else {
            throw new IllegalArgumentException();
        }
    }
    
    private static void parseArgs(String[] args) {
        if (args.length < 2 || args.length > 4) {
            throw new IllegalArgumentException();
        }
        metric = args[0];
        sourceEmbedding = Integer.parseInt(args[1]);
        if (sourceEmbedding < 1) {
            throw new IllegalArgumentException();
        }
        System.out.printf("# l_HISTORY = %d%n", sourceEmbedding);
        if (args.length >= 3) {
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
    }
    
    private static void calculateStorage() throws Exception {
        MutualInfoCalculatorMultiVariate calculator = new MutualInfoCalculatorMultiVariateKraskov1();
        Utility.setProperties(calculator, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                if (ensemble.getInternalNeuronCount() == 0) {
                    System.out.printf("%d 0%n", ensemble.getAgentIndex());
                    continue;
                }
                calculator.initialise(sourceEmbedding * ensemble.getInternalNeuronCount(), ensemble.getInternalNeuronCount());
                calculator.startAddObservations();
                for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
                    double[][] data = timeSeries.get(ensemble.getInternalNeuronIndices());
                    calculator.addObservations(
                        MatrixUtils.makeDelayEmbeddingVector(data, sourceEmbedding, sourceEmbedding - 1, data.length - sourceEmbedding),
                        MatrixUtils.selectRows(data, sourceEmbedding, data.length - sourceEmbedding));
                }
                calculator.finaliseAddObservations();
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculator.computeAverageLocalOfObservations());
            }
        }
    }
    
    private static void calculateTransferOrModification() throws Exception {
        ConditionalTransferEntropyCalculatorMultiVariate calculator = new ConditionalTransferEntropyCalculatorMultiVariate(sourceEmbedding, targetEmbedding, conditionalEmbedding);
        Utility.setProperties(calculator, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double value;
                if (metric.equals("transfer")) {
                    value = calculator.calculate(ensemble, ensemble.getInputNeuronIndices(), ensemble.getOutputNeuronIndices());
                } else if (metric.equals("modification")) {
                    value = calculator.calculate(ensemble, ensemble.getInternalNeuronIndices(), ensemble.getOutputNeuronIndices(), ensemble.getInputNeuronIndices());
                } else {
                    throw new IllegalArgumentException();
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), value);
            }
        }
    }
}
