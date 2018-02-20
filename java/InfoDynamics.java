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
                int[][][] data = discretize(ensemble);
                double[][][] locals = new double[ensemble.getProcessingNeuronCount()][ensemble.size()][];
                System.out.printf("%d S %g%n", agentIndex, getStorage(ensemble, data, locals));
                System.out.printf("%d T %g%n", agentIndex, getTransfer(ensemble, data, locals));
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
    
    private static int[][][] discretize(TimeSeriesEnsemble ensemble) {
        int[][][] data = new int[ensemble.getNeuronCount()][ensemble.size()][];
        for (int neuronIndex : ensemble.getNeuronIndices()) {
            int[][] columns = data[neuronIndex];
            int columnIndex = 0;
            for (TimeSeries timeSeries : ensemble) {
                columns[columnIndex++] = timeSeries.getColumnDiscrete(neuronIndex, base);
            }
        }
        return data;
    }
    
    private static double getStorage(TimeSeriesEnsemble ensemble, int[][][] data, double[][][] locals) throws Exception {
        int count = 0;
        double sum = 0.0;
        int[] neuronIndices = ensemble.getProcessingNeuronIndices();
        for (int index = 0; index < neuronIndices.length; index++) {
            int neuronIndex = neuronIndices[index];
            int[][] columns = data[neuronIndex];
            storageCalculator.initialise();
            for (int columnIndex = 0; columnIndex < ensemble.size(); columnIndex++) {
                storageCalculator.addObservations(columns[columnIndex]);
            }
            for (int columnIndex = 0; columnIndex < ensemble.size(); columnIndex++) {
                double[] storages = storageCalculator.computeLocalFromPreviousObservations(columns[columnIndex]);
                locals[index][columnIndex] = storages;
                count += storages.length - embedding;
                sum += MatrixUtils.sum(storages);
            }
        }
        return sum / count;
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble, int[][][] data, double[][][] locals) throws Exception {
        int count = 0;
        double sum = 0.0;
        int[] postNeuronIndices = ensemble.getProcessingNeuronIndices();
        for (int postIndex = 0; postIndex < postNeuronIndices.length; postIndex++) {
            int postNeuronIndex = postNeuronIndices[postIndex];
            int[][] postColumns = data[postNeuronIndex];
            int[] preNeuronIndices = ensemble.getPreNeuronIndices(postNeuronIndex);
            if (preNeuronIndices.length == 0) {
                continue;
            }
            for (int preIndex = 0; preIndex < preNeuronIndices.length; preIndex++) {
                int preNeuronIndex = preNeuronIndices[preIndex];
                int[][] preColumns = data[preNeuronIndex];
                transferCalculator.initialise();
                for (int columnIndex = 0; columnIndex < ensemble.size(); columnIndex++) {
                    transferCalculator.addObservations(preColumns[columnIndex], postColumns[columnIndex]);
                }
                for (int columnIndex = 0; columnIndex < ensemble.size(); columnIndex++) {
                    double[] transfers = transferCalculator.computeLocalFromPreviousObservations(preColumns[columnIndex], postColumns[columnIndex]);
                    MatrixUtils.addInPlace(locals[postIndex][columnIndex], transfers);
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
        for (double[][] columns : locals) {
            for (double[] column : columns) {
                count += column.length - embedding;
                for (double modification : column) {
                    modifications[TRIVIAL] += Math.max(modification, 0.0);
                    modifications[NONTRIVIAL] += Math.min(modification, 0.0);
                }
            }
        }
        modifications[TRIVIAL] /= count;
        modifications[NONTRIVIAL] /= count;
        return modifications;
    }
}
