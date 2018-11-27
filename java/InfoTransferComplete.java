import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;
import java.util.*;

public class InfoTransferComplete {
    private static boolean gpu;
    private static int embedding;
    private static int count;
    private static ConditionalMutualInfoCalculatorMultiVariateKraskov1 calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s GPU EMBEDDING COUNT%n", InfoTransferComplete.class.getSimpleName());
            return;
        }
        calculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        if (gpu) {
            calculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, Boolean.TRUE.toString());
        }
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            System.out.printf("# count = %d%n", count);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                List<Synapse> synapses = new ArrayList<Synapse>();
                for (Synapse synapse : ensemble.getSynapses()) {
                    synapses.add(synapse);
                }
                Collections.shuffle(synapses);
                double sum = 0.0;
                int index = 0;
                while (index < count && index < synapses.size()) {
                    Synapse synapse = synapses.get(index);
                    sum += getTransfer(ensemble, synapse.getPreNeuronIndex(), synapse.getPostNeuronIndex());
                    index++;
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), index, sum);
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 3;
            int index = 0;
            gpu = Boolean.parseBoolean(args[index++]);
            embedding = Integer.parseInt(args[index++]);
            assert embedding > 0;
            count = Integer.parseInt(args[index++]);
            assert count > 0;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex) throws Exception {
        int[] conditionalNeuronIndices = ensemble.getPreNeuronIndices(postNeuronIndex, preNeuronIndex);
        calculator.initialise(1, 1, embedding + conditionalNeuronIndices.length);
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            int length = timeSeries.size() - embedding;
            double[][] source = timeSeries.getColumns(new int[] { preNeuronIndex });
            double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
            double[][] conditional = timeSeries.getColumns(conditionalNeuronIndices);
            calculator.addObservations(
                MatrixUtils.selectRows(source, embedding - 1, length),
                MatrixUtils.selectRows(target, embedding, length),
                MatrixUtils.appendColumns(
                    MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, length),
                    MatrixUtils.selectRows(conditional, embedding - 1, length)));
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
