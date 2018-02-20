import infodynamics.measures.discrete.*;
import infodynamics.utils.*;

public class InfoDynamics {
    private static final int TRIVIAL = 0;
    private static final int NONTRIVIAL = 1;
    
    private static int base;
    private static int embedding;
    private static ActiveInformationCalculatorDiscrete storageCalculator;
    private static TransferEntropyCalculatorDiscrete transferCalculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s BASE EMBEDDING%n", InfoDynamics.class.getSimpleName());
            return;
        }
        storageCalculator = new ActiveInformationCalculatorDiscrete(base, embedding);
        transferCalculator = new TransferEntropyCalculatorDiscrete(base, embedding);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# base = %d%n", base);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                int agentIndex = ensemble.getAgentIndex();
                double[][][] locals = new double[ensemble.getProcessingNeuronCount()][ensemble.size()][];
                System.out.printf("%d S %g%n", agentIndex, getStorage(ensemble, locals));
                System.out.printf("%d T %g%n", agentIndex, getTransfer(ensemble, locals));
                double[] modifications = getModifications(locals);
                System.out.printf("%d M %g %g%n", agentIndex, modifications[TRIVIAL], modifications[NONTRIVIAL]);
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 2;
            base = Integer.parseInt(args[0]);
            assert base > 1;
            embedding = Integer.parseInt(args[1]);
            assert embedding > 0;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static double getStorage(TimeSeriesEnsemble ensemble, double[][][] locals) throws Exception {
        int count = 0;
        double sum = 0.0;
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        for (int index = 0; index < neuronIndices.length; index++) {
            int neuronIndex = neuronIndices[index];
            storageCalculator.initialise();
            for (TimeSeries timeSeries : ensemble) {
                storageCalculator.addObservations(timeSeries.getColumnDiscrete(neuronIndex, base));
            }
            int ensembleIndex = 0;
            for (TimeSeries timeSeries : ensemble) {
                double[] storages = storageCalculator.computeLocalFromPreviousObservations(timeSeries.getColumnDiscrete(neuronIndex, base));
                locals[index][ensembleIndex++] = storages;
                count += storages.length - embedding;
                sum += MatrixUtils.sum(storages);
            }
        }
        return sum / count;
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble, double[][][] locals) throws Exception {
        int count = 0;
        double sum = 0.0;
        int[] postNeuronIndices = ensemble.getProcessingNeuronIndices();
        for (int postIndex = 0; postIndex < postNeuronIndices.length; postIndex++) {
            int postNeuronIndex = postNeuronIndices[postIndex];
            int[] preNeuronIndices = ensemble.getPreNeuronIndices(postNeuronIndex);
            if (preNeuronIndices.length == 0) {
                continue;
            }
            for (int preIndex = 0; preIndex < preNeuronIndices.length; preIndex++) {
                int preNeuronIndex = preNeuronIndices[preIndex];
                transferCalculator.initialise();
                for (TimeSeries timeSeries : ensemble) {
                    transferCalculator.addObservations(
                        timeSeries.getColumnDiscrete(preNeuronIndex, base),
                        timeSeries.getColumnDiscrete(postNeuronIndex, base));
                }
                int ensembleIndex = 0;
                for (TimeSeries timeSeries : ensemble) {
                    double[] transfers = transferCalculator.computeLocalFromPreviousObservations(
                        timeSeries.getColumnDiscrete(preNeuronIndex, base),
                        timeSeries.getColumnDiscrete(postNeuronIndex, base));
                    MatrixUtils.addInPlace(locals[postIndex][ensembleIndex++], transfers);
                    count += transfers.length - embedding;
                    sum += MatrixUtils.sum(transfers);
                }
            }
        }
        return count == 0 ? 0.0 : sum / count;
    }
    
    private static double[] getModifications(double[][][] locals) {
        int count = 0;
        double[] modifications = new double[2];
        for (double[][] local : locals) {
            for (double[] values : local) {
                count += values.length - embedding;
                for (double value : values) {
                    modifications[TRIVIAL] += Math.max(value, 0.0);
                    modifications[NONTRIVIAL] += Math.min(value, 0.0);
                }
            }
        }
        modifications[TRIVIAL] /= count;
        modifications[NONTRIVIAL] /= count;
        return modifications;
    }
}
