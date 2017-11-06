import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;
import java.util.*;

public class InfoDynamics {
    private static final int TRIVIAL = 0;
    private static final int NONTRIVIAL = 1;
    
    private static int embedding;
    private static MutualInfoCalculatorMultiVariate miCalculator;
    private static ConditionalMutualInfoCalculatorMultiVariate cmiCalculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s EMBEDDING%n", InfoDynamics.class.getSimpleName());
            return;
        }
        miCalculator = new MutualInfoCalculatorMultiVariateKraskov1();
        cmiCalculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double[][] storages = getStorages(ensemble);
                System.out.printf("%d S %g%n", ensemble.getAgentIndex(), MatrixUtils.mean(storages));
                System.out.printf("%d T %g%n", ensemble.getAgentIndex(), getTransfer(ensemble));
                double[] modifications = getModifications(ensemble, storages);
                System.out.printf("%d M %g %g%n", ensemble.getAgentIndex(), modifications[TRIVIAL], modifications[NONTRIVIAL]);
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 1;
            embedding = Integer.parseInt(args[0]);
            assert embedding > 0;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static double[][] getStorages(TimeSeriesEnsemble ensemble) throws Exception {
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        double[][] storages = new double[ensemble.size() * (ensemble.getFirst().size() - embedding)][neuronIndices.length];
        for (int index = 0; index < neuronIndices.length; index++) {
            int neuronIndex = neuronIndices[index];
            miCalculator.initialise(embedding, 1);
            miCalculator.startAddObservations();
            for (TimeSeries timeSeries : ensemble) {
                double[][] data = timeSeries.getColumns(new int[] { neuronIndex });
                miCalculator.addObservations(embedData(data), selectData(data));
            }
            miCalculator.finaliseAddObservations();
            MatrixUtils.copyIntoColumn(storages, index, miCalculator.computeLocalOfPreviousObservations());
        }
        return storages;
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble) throws Exception {
        int[] postNeuronIndices = ensemble.getProcessingNeuronIndices();
        double[] transfers = new double[postNeuronIndices.length];
        for (int postIndex = 0; postIndex < postNeuronIndices.length; postIndex++) {
            int postNeuronIndex = postNeuronIndices[postIndex];
            int[] preNeuronIndices = getPreNeuronIndices(ensemble, postNeuronIndex);
            if (preNeuronIndices.length == 0) {
                transfers[postIndex] = 0.0;
                continue;
            }
            cmiCalculator.initialise(embedding * preNeuronIndices.length, 1, embedding);
            cmiCalculator.startAddObservations();
            for (TimeSeries timeSeries : ensemble) {
                double[][] source = timeSeries.getColumns(preNeuronIndices);
                double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
                cmiCalculator.addObservations(embedData(source), selectData(target), embedData(target));
            }
            cmiCalculator.finaliseAddObservations();
            transfers[postIndex] = cmiCalculator.computeAverageLocalOfObservations();
        }
        return MatrixUtils.mean(transfers);
    }
    
    private static double[] getModifications(TimeSeriesEnsemble ensemble, double[][] storages) throws Exception {
        int[] postNeuronIndices = ensemble.getProcessingNeuronIndices();
        double[] modifications = new double[2];
        for (int postIndex = 0; postIndex < postNeuronIndices.length; postIndex++) {
            int postNeuronIndex = postNeuronIndices[postIndex];
            int[] preNeuronIndices = getPreNeuronIndices(ensemble, postNeuronIndex);
            double[][] transfers = new double[storages.length][preNeuronIndices.length];
            for (int preIndex = 0; preIndex < preNeuronIndices.length; preIndex++) {
                int preNeuronIndex = preNeuronIndices[preIndex];
                cmiCalculator.initialise(embedding, 1, embedding);
                cmiCalculator.startAddObservations();
                for (TimeSeries timeSeries : ensemble) {
                    double[][] source = timeSeries.getColumns(new int[] { preNeuronIndex });
                    double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
                    cmiCalculator.addObservations(embedData(source), selectData(target), embedData(target));
                }
                cmiCalculator.finaliseAddObservations();
                MatrixUtils.copyIntoColumn(transfers, preIndex, cmiCalculator.computeLocalOfPreviousObservations());
            }
            for (int time = 0; time < storages.length; time++) {
                double modification = storages[time][postIndex];
                for (int preIndex = 0; preIndex < preNeuronIndices.length; preIndex++) {
                    modification += transfers[time][preIndex];
                }
                if (modification >= 0.0) {
                    modifications[TRIVIAL] += modification;
                } else {
                    modifications[NONTRIVIAL] += modification;
                }
            }
        }
        int count = storages.length * postNeuronIndices.length;
        modifications[TRIVIAL] /= count;
        modifications[NONTRIVIAL] /= count;
        return modifications;
    }
    
    private static double[][] embedData(double[][] data) throws Exception {
        return MatrixUtils.makeDelayEmbeddingVector(data, embedding, embedding - 1, data.length - embedding);
    }
    
    private static double[][] selectData(double[][] data) {
        return MatrixUtils.selectRows(data, embedding, data.length - embedding);
    }
    
    private static int[] getPreNeuronIndices(TimeSeriesEnsemble ensemble, int postNeuronIndex) {
        Collection<Integer> preNeuronIndices = new LinkedList<Integer>();
        for (Synapse synapse : ensemble.getSynapses()) {
            if (synapse.getPostNeuronIndex() == postNeuronIndex) {
                assert synapse.getPreNeuronIndex() != postNeuronIndex;
                preNeuronIndices.add(synapse.getPreNeuronIndex());
            }
        }
        return toPrimitive(preNeuronIndices);
    }
    
    private static int[] toPrimitive(Collection<Integer> values) {
        int[] result = new int[values.size()];
        int index = 0;
        for (int value : values) {
            result[index] = value;
            index++;
        }
        return result;
    }
}
