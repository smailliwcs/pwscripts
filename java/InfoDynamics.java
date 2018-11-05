import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoDynamics {
    private static class Calculator extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
        public void addObservations(double[][][] observations) throws Exception {
            addObservations(observations[0], observations[1], observations[2]);
        }
        
        @Override
        public double[] computeLocalUsingPreviousObservations(double[][] source, double[][] target, double[][] conditional) throws Exception {
            if (normalise) {
                source = MatrixUtils.normaliseIntoNewArray(source, var1Means, var1Stds);
                target = MatrixUtils.normaliseIntoNewArray(target, var2Means, var2Stds);
                conditional = MatrixUtils.normaliseIntoNewArray(conditional, condMeans, condStds);
            }
            return computeFromObservations(true, new double[][][] { source, target, conditional });
        }
        
        public double[] computeLocalUsingPreviousObservations(double[][][] observations) throws Exception {
            return computeLocalUsingPreviousObservations(observations[0], observations[1], observations[2]);
        }
    }
    
    private static class Result {
        public int count;
        public double sum;
        
        public void add(Result result) {
            count += result.count;
            sum += result.sum;
        }
    }
    
    private static boolean single;
    private static boolean gpu;
    private static int embedding;
    private static String mode;
    private static Calculator calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s [--single] GPU EMBEDDING [MODE]%n", InfoDynamics.class.getSimpleName());
            return;
        }
        calculator = new Calculator();
        if (gpu) {
            calculator.setProperty(ConditionalMutualInfoCalculatorMultiVariateKraskov.PROP_USE_GPU, Boolean.TRUE.toString());
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
                if (mode == null || mode.equals("S") || mode.equals("M")) {
                    getStorage(ensemble, locals);
                }
                if (mode == null || mode.equals("T")) {
                    getCompleteTransfer(ensemble);
                }
                if (mode == null || mode.equals("M")) {
                    getApparentTransfer(ensemble, locals);
                    getModification(ensemble, locals);
                }
            }
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length >= 2 && args.length <= 3;
            int index = 0;
            if (args[index].equals("--single")) {
                single = true;
                index++;
            }
            gpu = Boolean.parseBoolean(args[index++]);
            embedding = Integer.parseInt(args[index++]);
            assert embedding > 0;
            if (index < args.length) {
                mode = args[index++];
            }
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static void getStorage(TimeSeriesEnsemble ensemble, double[][] locals) throws Exception {
        if (single) {
            System.out.println("# S");
        }
        Result result = getStorage(ensemble, ensemble.getProcessingNeuronIndices(), locals);
        if (!single) {
            System.out.printf("%d S %d %g%n", ensemble.getAgentIndex(), result.count, result.sum);
        }
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
        calculator.initialise(embedding, 1, 0);
        calculator.startAddObservations();
        for (int index = 0; index < ensemble.size(); index++) {
            if (single && index == ensemble.size() - 1) {
                break;
            }
            TimeSeries timeSeries = ensemble.get(index);
            calculator.addObservations(getStorageObservations(timeSeries, neuronIndex));
        }
        calculator.finaliseAddObservations();
        double[] local;
        if (single) {
            TimeSeries timeSeries = ensemble.get(ensemble.size() - 1);
            local = calculator.computeLocalUsingPreviousObservations(getStorageObservations(timeSeries, neuronIndex));
            System.out.printf("%d ", neuronIndex);
            MatrixUtils.printArray(System.out, local);
            System.out.println();
        } else {
            local = calculator.computeLocalOfPreviousObservations();
        }
        locals[ensemble.getProcessingNeuronOffset(neuronIndex)] = local;
        return MatrixUtils.mean(local);
    }
    
    private static double[][][] getStorageObservations(TimeSeries timeSeries, int neuronIndex) throws Exception {
        int length = timeSeries.size() - embedding;
        double[][] data = timeSeries.getColumns(new int[] { neuronIndex });
        return new double[][][] {
            MatrixUtils.makeDelayEmbeddingVector(data, embedding, embedding - 1, length),
            MatrixUtils.selectRows(data, embedding, length),
            new double[length][0]
        };
    }
    
    private static void getCompleteTransfer(TimeSeriesEnsemble ensemble) throws Exception {
        if (single) {
            System.out.println("# CT");
        }
        Result result = new Result();
        for (Nerve nerve : ensemble.getInputNerves()) {
            result.add(getCompleteTransfer(ensemble, nerve.getName(), nerve.getNeuronIndices()));
        }
        result.add(getCompleteTransfer(ensemble, "Internal", ensemble.getProcessingNeuronIndices()));
        if (!single) {
            System.out.printf("%d T Total %d %g%n", ensemble.getAgentIndex(), result.count, result.sum);
        }
    }
    
    private static Result getCompleteTransfer(TimeSeriesEnsemble ensemble, String label, int[] preNeuronIndices) throws Exception {
        Result result = new Result();
        for (int preNeuronIndex : preNeuronIndices) {
            for (int postNeuronIndex : ensemble.getPostNeuronIndices(preNeuronIndex)) {
                result.count++;
                result.sum += getCompleteTransfer(ensemble, preNeuronIndex, postNeuronIndex);
            }
        }
        if (!single) {
            System.out.printf("%d T %s %d %g%n", ensemble.getAgentIndex(), label, result.count, result.sum);
        }
        return result;
    }
    
    private static double getCompleteTransfer(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex) throws Exception {
        int[] conditionalNeuronIndices = ensemble.getPreNeuronIndices(postNeuronIndex, preNeuronIndex);
        calculator.initialise(1, 1, embedding + conditionalNeuronIndices.length);
        calculator.startAddObservations();
        for (int index = 0; index < ensemble.size(); index++) {
            if (single && index == ensemble.size() - 1) {
                break;
            }
            TimeSeries timeSeries = ensemble.get(index);
            calculator.addObservations(getCompleteTransferObservations(timeSeries, preNeuronIndex, postNeuronIndex, conditionalNeuronIndices));
        }
        calculator.finaliseAddObservations();
        double[] local;
        if (single) {
            TimeSeries timeSeries = ensemble.get(ensemble.size() - 1);
            local = calculator.computeLocalUsingPreviousObservations(getCompleteTransferObservations(timeSeries, preNeuronIndex, postNeuronIndex, conditionalNeuronIndices));
            System.out.printf("%d %d ", preNeuronIndex, postNeuronIndex);
            MatrixUtils.printArray(System.out, local);
            System.out.println();
        } else {
            local = calculator.computeLocalOfPreviousObservations();
        }
        return MatrixUtils.mean(local);
    }
    
    private static double[][][] getCompleteTransferObservations(TimeSeries timeSeries, int preNeuronIndex, int postNeuronIndex, int[] conditionalNeuronIndices) throws Exception {
        int length = timeSeries.size() - embedding;
        double[][] source = timeSeries.getColumns(new int[] { preNeuronIndex });
        double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
        double[][] conditional = timeSeries.getColumns(conditionalNeuronIndices);
        return new double[][][] {
            MatrixUtils.selectRows(source, embedding - 1, length),
            MatrixUtils.selectRows(target, embedding, length),
            MatrixUtils.appendColumns(
                MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, length),
                MatrixUtils.selectRows(conditional, embedding - 1, length))
        };
    }
    
    private static void getApparentTransfer(TimeSeriesEnsemble ensemble, double[][] locals) throws Exception {
        if (single) {
            System.out.println("# AT");
        }
        for (Synapse synapse : ensemble.getSynapses()) {
            getApparentTransfer(ensemble, synapse.getPreNeuronIndex(), synapse.getPostNeuronIndex(), locals);
        }
    }
    
    private static double getApparentTransfer(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex, double[][] locals) throws Exception {
        calculator.initialise(1, 1, embedding);
        calculator.startAddObservations();
        for (int index = 0; index < ensemble.size(); index++) {
            if (single && index == ensemble.size() - 1) {
                break;
            }
            TimeSeries timeSeries = ensemble.get(ensemble.size() - 1);
            calculator.addObservations(getApparentTransferObservations(timeSeries, preNeuronIndex, postNeuronIndex));
        }
        calculator.finaliseAddObservations();
        double[] local;
        if (single) {
            TimeSeries timeSeries = ensemble.get(ensemble.size() - 1);
            local = calculator.computeLocalUsingPreviousObservations(getApparentTransferObservations(timeSeries, preNeuronIndex, postNeuronIndex));
            System.out.printf("%d %d ", preNeuronIndex, postNeuronIndex);
            MatrixUtils.printArray(System.out, local);
            System.out.println();
        } else {
            local = calculator.computeLocalOfPreviousObservations();
        }
        MatrixUtils.addInPlace(locals[ensemble.getProcessingNeuronOffset(postNeuronIndex)], local);
        return MatrixUtils.mean(local);
    }
    
    private static double[][][] getApparentTransferObservations(TimeSeries timeSeries, int preNeuronIndex, int postNeuronIndex) throws Exception {
        int length = timeSeries.size() - embedding;
        double[][] source = timeSeries.getColumns(new int[] { preNeuronIndex });
        double[][] target = timeSeries.getColumns(new int[] { postNeuronIndex });
        return new double[][][] {
            MatrixUtils.selectRows(source, embedding - 1, length),
            MatrixUtils.selectRows(target, embedding, length),
            MatrixUtils.makeDelayEmbeddingVector(target, embedding, embedding - 1, length)
        };
    }
    
    private static void getModification(TimeSeriesEnsemble ensemble, double[][] locals) {
        if (single) {
            int[] neuronIndices = ensemble.getProcessingNeuronIndices();
            System.out.println("# M");
            for (int index = 0; index < locals.length; index++) {
                System.out.printf("%d ", neuronIndices[index]);
                MatrixUtils.printArray(System.out, locals[index]);
                System.out.println();
            }
        } else {
            getModification(ensemble, "Trivial", true, false, locals);
            getModification(ensemble, "Nontrivial", false, true, locals);
            getModification(ensemble, "Total", true, true, locals);
        }
    }
    
    private static void getModification(TimeSeriesEnsemble ensemble, String label, boolean positive, boolean negative, double[][] locals) {
        Result result = new Result();
        for (double[] local : locals) {
            double sum = 0.0;
            for (double value : local) {
                if ((value > 0.0 && positive) || (value < 0.0 && negative)) {
                    sum += value;
                }
            }
            result.count++;
            result.sum += sum / local.length;
        }
        System.out.printf("%d M %s %d %g%n", ensemble.getAgentIndex(), label, result.count, result.sum);
    }
}
