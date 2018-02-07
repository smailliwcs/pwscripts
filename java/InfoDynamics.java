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
                int agentIndex = ensemble.getAgentIndex();
                int inputNeuronCount = ensemble.getInputNeuronCount();
                double[] storage = getStorage(ensemble);
                System.out.printf("%d S %g%n", agentIndex, MatrixUtils.mean(storage));
                Collection<double[]> transfers = new LinkedList<double[]>();
                double[] transfer;
                for (Nerve nerve : ensemble.getNerves()) {
                    int[] neuronIndices = nerve.getNeuronIndices();
                    if (neuronIndices[neuronIndices.length - 1] >= inputNeuronCount) {
                        assert neuronIndices[0] >= inputNeuronCount;
                        break;
                    }
                    transfer = getTransfer(ensemble, neuronIndices);
                    System.out.printf("%d AT %s %g%n", agentIndex, nerve.getName(), MatrixUtils.mean(transfer));
                    transfers.add(transfer);
                }
                transfer = getTransfer(ensemble, ensemble.getInputNeuronIndices());
                System.out.printf("%d CT %g%n", agentIndex, MatrixUtils.mean(transfer));
                double[][] modification = getModification(storage, transfers);
                System.out.printf("%d M %g %g%n", agentIndex, MatrixUtils.mean(modification[TRIVIAL]), MatrixUtils.mean(modification[NONTRIVIAL]));
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
    
    private static double[] getStorage(TimeSeriesEnsemble ensemble) throws Exception {
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        miCalculator.initialise(neuronIndices.length * embedding, neuronIndices.length);
        miCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] data = timeSeries.getColumns(neuronIndices);
            miCalculator.addObservations(
                MatrixUtils.makeDelayEmbeddingVector(data, embedding, embedding - 1, data.length - embedding),
                MatrixUtils.selectRows(data, embedding, data.length - embedding));
        }
        miCalculator.finaliseAddObservations();
        return miCalculator.computeLocalOfPreviousObservations();
    }
    
    private static double[] getTransfer(TimeSeriesEnsemble ensemble, int[] sourceNeuronIndices) throws Exception {
        int[] targetNeuronIndices = ensemble.getProcessingNeuronIndices();
        cmiCalculator.initialise(sourceNeuronIndices.length * embedding, targetNeuronIndices.length, targetNeuronIndices.length * embedding);
        cmiCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] source = timeSeries.getColumns(sourceNeuronIndices);
            double[][] target = timeSeries.getColumns(targetNeuronIndices);
            cmiCalculator.addObservations(
                MatrixUtils.makeDelayEmbeddingVector(source, embedding, embedding, source.length - embedding),
                MatrixUtils.selectRows(target, embedding, target.length - embedding),
                MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, target.length - embedding));
        }
        cmiCalculator.finaliseAddObservations();
        return cmiCalculator.computeLocalOfPreviousObservations();
    }
    
    private static double[][] getModification(double[] storage, Collection<double[]> transfers) {
        double[][] modification = new double[2][storage.length];
        for (int time = 0; time < storage.length; time++) {
            double value = storage[time];
            for (double[] transfer : transfers) {
                value += transfer[time];
            }
            modification[TRIVIAL][time] = Math.max(value, 0.0);
            modification[NONTRIVIAL][time] = Math.min(value, 0.0);
        }
        return modification;
    }
}
