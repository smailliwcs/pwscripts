import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoDynamics {
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
            String gpuLibraryPath = System.getenv("JIDT_GPU_LIBRARY_PATH");
            storageCalculator.setProperty(MutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, useGpu);
            storageCalculator.setProperty(MutualInfoCalculatorMultiVariateKraskov.PROP_GPU_LIBRARY_PATH, gpuLibraryPath);
            transferCalculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, useGpu);
            transferCalculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_GPU_LIBRARY_PATH, gpuLibraryPath);
        }
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.printf("# embedding = %d%n", embedding);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                int agentIndex = ensemble.getAgentIndex();
                int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
                double[][] locals = new double[processingNeuronIndices.length][];
                {
                    double sum = 0.0;
                    int count = 0;
                    for (int neuronIndex : processingNeuronIndices) {
                        sum += getStorage(ensemble, neuronIndex, locals);
                        count++;
                    }
                    if (mode == null || mode.equals("S")) {
                        double storage = sum / count;
                        System.out.printf("%d S %g%n", agentIndex, storage);
                    }
                }
                if (mode == null || mode.equals("T")) {
                    double sum = 0.0;
                    int count = 0;
                    for (Nerve nerve : ensemble.getInputNerves()) {
                        double nerveSum = 0.0;
                        int nerveCount = 0;
                        for (int preNeuronIndex : nerve.getNeuronIndices()) {
                            for (int postNeuronIndex : ensemble.getPostNeuronIndices(preNeuronIndex)) {
                                double value = getTransfer(ensemble, preNeuronIndex, postNeuronIndex, locals);
                                sum += value;
                                count++;
                                nerveSum += value;
                                nerveCount++;
                            }
                        }
                        double nerveTransfer = nerveCount > 0 ? nerveSum / nerveCount : 0.0;
                        System.out.printf("%d T %s %g%n", agentIndex, nerve.getName(), nerveTransfer);
                    }
                    double transfer = count > 0 ? sum / count : 0.0;
                    System.out.printf("%d T Total %g%n", agentIndex, transfer);
                }
                if (mode == null) {
                    double positiveSum = 0.0;
                    double negativeSum = 0.0;
                    int count = 0;
                    for (double[] local : locals) {
                        for (double value : local) {
                            positiveSum += Math.max(value, 0.0);
                            negativeSum += Math.min(value, 0.0);
                            count++;
                        }
                    }
                    double trivialModification = positiveSum / count;
                    double nontrivialModification = negativeSum / count;
                    System.out.printf("%d M %g %g%n", agentIndex, trivialModification, nontrivialModification);
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
}
