import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoDynamics {
    private static class Result {
        public int count;
        public double sum;
        
        public void add(Result result) {
            count += result.count;
            sum += result.sum;
        }
        
        public double getMean() {
            return count == 0 ? 0.0 : sum / count;
        }
    }
    
    private static boolean gpu;
    private static int embedding;
    private static String mode;
    private static MutualInfoCalculatorMultiVariateKraskov storageCalculator;
    private static ConditionalMutualInfoCalculatorMultiVariateKraskov transferCalculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s GPU EMBEDDING [MODE]%n", InfoDynamics.class.getSimpleName());
            return;
        }
        storageCalculator = new MutualInfoCalculatorMultiVariateKraskov1();
        transferCalculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
        if (gpu) {
            String useGpu = Boolean.TRUE.toString();
            storageCalculator.setProperty(MutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, useGpu);
            transferCalculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, useGpu);
        }
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double[][] locals = new double[ensemble.getProcessingNeuronCount()][];
                if (mode == null || mode.equals("S")) {
                    getStorage(ensemble, locals);
                }
                if (mode == null || mode.equals("T")) {
                    getTransfer(ensemble, locals);
                }
                if (mode == null) {
                    getModification(ensemble, locals);
                }
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length >= 2 && args.length <= 3;
            gpu = Boolean.parseBoolean(args[0]);
            embedding = Integer.parseInt(args[1]);
            assert embedding > 0;
            if (args.length > 2) {
                mode = args[2];
            }
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static void getStorage(TimeSeriesEnsemble ensemble, double[][] locals) throws Exception {
        Result result = getStorage(ensemble, ensemble.getProcessingNeuronIndices(), locals);
        System.out.printf("%d S %g%n", ensemble.getAgentIndex(), result.getMean());
    }
    
    private static Result getStorage(TimeSeriesEnsemble ensemble, int[] neuronIndices, double[][] locals) throws Exception {
        Result result = new Result();
        for (int neuronIndex : neuronIndices) {
            result.count++;
            result.sum += getStorage(ensemble, neuronIndex, locals);
        }
        return result;
    }
    
    private static double getStorage(TimeSeriesEnsemble ensemble, int neuronIndex, double[][] locals) throws Exception {
        storageCalculator.initialise(embedding, 1);
        storageCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] data = timeSeries.getColumns(new int[] { neuronIndex });
            storageCalculator.addObservations(
                MatrixUtils.makeDelayEmbeddingVector(data, embedding, embedding - 1, timeSeries.size() - embedding),
                MatrixUtils.selectRows(data, embedding, timeSeries.size() - embedding));
        }
        storageCalculator.finaliseAddObservations();
        double[] local = storageCalculator.computeLocalOfPreviousObservations();
        locals[ensemble.getProcessingNeuronOffset(neuronIndex)] = local;
        return MatrixUtils.mean(local);
    }
    
    private static void getTransfer(TimeSeriesEnsemble ensemble, double[][] locals) throws Exception {
        Result result = new Result();
        for (Nerve nerve : ensemble.getInputNerves()) {
            result.add(getTransfer(ensemble, nerve.getName(), nerve.getNeuronIndices(), locals));
        }
        result.add(getTransfer(ensemble, "Internal", ensemble.getProcessingNeuronIndices(), locals));
        System.out.printf("%d T Total %g%n", ensemble.getAgentIndex(), result.getMean());
    }
    
    private static Result getTransfer(TimeSeriesEnsemble ensemble, String label, int[] preNeuronIndices, double[][] locals) throws Exception {
        Result result = new Result();
        for (int preNeuronIndex : preNeuronIndices) {
            for (int postNeuronIndex : ensemble.getPostNeuronIndices(preNeuronIndex)) {
                result.count++;
                result.sum += getTransfer(ensemble, preNeuronIndex, postNeuronIndex, locals);
            }
        }
        System.out.printf("%d T %s %g%n", ensemble.getAgentIndex(), label, result.getMean());
        return result;
    }
    
    private static double getTransfer(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex, double[][] locals) throws Exception {
        transferCalculator.initialise(1, 1, embedding);
        transferCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble) {
            double[][] source = timeSeries.getColumns(new int[] { preNeuronIndex });
            double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
            transferCalculator.addObservations(
                MatrixUtils.selectRows(source, embedding - 1, timeSeries.size() - embedding),
                MatrixUtils.selectRows(target, embedding, timeSeries.size() - embedding),
                MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, timeSeries.size() - embedding));
        }
        transferCalculator.finaliseAddObservations();
        double[] local = transferCalculator.computeLocalOfPreviousObservations();
        MatrixUtils.addInPlace(locals[ensemble.getProcessingNeuronOffset(postNeuronIndex)], local);
        return MatrixUtils.mean(local);
    }
    
    private static void getModification(TimeSeriesEnsemble ensemble, double[][] locals) {
        int count = 0;
        double positiveSum = 0.0;
        double negativeSum = 0.0;
        for (double[] local : locals) {
            for (double value : local) {
                count++;
                positiveSum += Math.max(value, 0.0);
                negativeSum += Math.min(value, 0.0);
            }
        }
        System.out.printf("%d M %g %g%n", ensemble.getAgentIndex(), positiveSum / count, negativeSum / count);
    }
}
