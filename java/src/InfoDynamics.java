import java.io.*;
import java.util.*;
import java.util.function.*;

import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class InfoDynamics {
    private static class Calculator extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
        private int embeddingLength;

        public Calculator(boolean useGpu, int embeddingLength) {
            setProperty(PROP_USE_GPU, Boolean.toString(useGpu));
            this.embeddingLength = embeddingLength;
        }

        public double[] getActiveInfoStorage(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
            initialise(embeddingLength, 1, 0);
            startAddObservations();
            for (TimeSeries observations : ensemble) {
                int count = observations.size() - embeddingLength;
                addObservations(
                        observations.embed(neuronIndex, embeddingLength, 0, count),
                        observations.slice(neuronIndex, embeddingLength, count),
                        new double[count][0]);
            }
            finaliseAddObservations();
            return computeLocalOfPreviousObservations();
        }

        public double[] getApparentTransferEntropy(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex)
                throws Exception {
            initialise(1, 1, embeddingLength);
            startAddObservations();
            for (TimeSeries observations : ensemble) {
                int count = observations.size() - embeddingLength;
                addObservations(
                        observations.slice(preNeuronIndex, embeddingLength - 1, count),
                        observations.slice(postNeuronIndex, embeddingLength, count),
                        observations.embed(postNeuronIndex, embeddingLength, 0, count));
            }
            finaliseAddObservations();
            return computeLocalOfPreviousObservations();
        }
    }

    private static class Arguments {
        private static String getUsage() {
            StringBuilder usage = new StringBuilder();
            usage.append("Usage: %s GPU EMBEDDING%n");
            usage.append("%n");
            usage.append("  GPU        Use GPU acceleration%n");
            usage.append("  EMBEDDING  Time series embedding length%n");
            return usage.toString();
        }

        public static Arguments parse(String[] args) {
            try (ArgumentParser parser = new ArgumentParser(getUsage(), InfoDynamics.class.getName(), args)) {
                boolean useGpu = parser.parse(Boolean::parseBoolean);
                int embeddingLength = parser.parse(
                        Integer::parseInt,
                        argument -> argument >= 1,
                        "Invalid time series embedding length");
                return new Arguments(useGpu, embeddingLength);
            }
        }

        public final boolean useGpu;
        public final int embeddingLength;

        private Arguments(boolean useGpu, int embeddingLength) {
            this.useGpu = useGpu;
            this.embeddingLength = embeddingLength;
        }

        public String toString() {
            StringBuilder result = new StringBuilder();
            result.append(String.format("# EMBEDDING = %d%n", embeddingLength));
            return result.toString();
        }
    }

    private static enum Metric {
        ACTIVE_INFO_STORAGE("AIS"),
        APPARENT_TRANSFER_ENTROPY("ATE"),
        SEPARABLE_INFO("SI");

        private String id;

        private Metric(String id) {
            this.id = id;
        }

        public String getId(String subset) {
            return String.format("%s[%s]", id, subset == null ? "*" : subset);
        }
    }

    private static Calculator calculator;
    private static TimeSeriesEnsemble ensemble;
    private static Map<Integer, double[]> locals;

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(args);
        calculator = new Calculator(arguments.useGpu, arguments.embeddingLength);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.print(arguments);
            System.out.println("agent metric count value");
            while (true) {
                ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                locals = new HashMap<Integer, double[]>();
                getActiveInfoStorage();
                getApparentTransferEntropy();
                getSeparableInfo();
            }
        }
    }

    private static void print(Metric metric, String subset, Result result) {
        System.out.printf(
                "%d %s %d %g%n",
                ensemble.getAgentId(),
                metric.getId(subset),
                result.getCount(),
                result.getSum());
    }

    private static Result getActiveInfoStorage() throws Exception {
        Result result = new Result();
        for (int neuronIndex : ensemble.getBrain().getNeuronIndices(Brain.Layer.PROCESSING)) {
            double[] local = calculator.getActiveInfoStorage(ensemble, neuronIndex);
            result.add(MatrixUtils.mean(local));
            locals.put(neuronIndex, local);
        }
        print(Metric.ACTIVE_INFO_STORAGE, null, result);
        return result;
    }

    private static Result getApparentTransferEntropy() throws Exception {
        Result result = new Result();
        result.add(getApparentTransferEntropy(Brain.Layer.INPUT));
        Result processingResult = new Result();
        processingResult.add(getApparentTransferEntropy(Brain.Layer.OUTPUT));
        processingResult.add(getApparentTransferEntropy(Brain.Layer.INTERNAL));
        print(Metric.APPARENT_TRANSFER_ENTROPY, Brain.Layer.PROCESSING.getName(), processingResult);
        result.add(processingResult);
        print(Metric.APPARENT_TRANSFER_ENTROPY, null, result);
        return result;
    }

    private static Result getApparentTransferEntropy(Brain.Layer layer) throws Exception {
        Result result = new Result();
        Collection<Integer> neuronIndices = ensemble.getBrain().getNeuronIndices(layer);
        for (Nerve nerve : ensemble.getBrain().getNerves(layer)) {
            Collection<Integer> nerveNeuronIndices = nerve.getNeuronIndices();
            Result nerveResult = getApparentTransferEntropy(nerveNeuronIndices);
            print(Metric.APPARENT_TRANSFER_ENTROPY, nerve.getName(), nerveResult);
            result.add(nerveResult);
            neuronIndices.removeAll(nerveNeuronIndices);
        }
        result.add(getApparentTransferEntropy(neuronIndices));
        print(Metric.APPARENT_TRANSFER_ENTROPY, layer.getName(), result);
        return result;
    }

    private static Result getApparentTransferEntropy(Collection<Integer> preNeuronIndices) throws Exception {
        Result result = new Result();
        for (int preNeuronIndex : preNeuronIndices) {
            for (int postNeuronIndex : ensemble.getBrain().getPostNeuronIndices(preNeuronIndex)) {
                double[] local = calculator.getApparentTransferEntropy(ensemble, preNeuronIndex, postNeuronIndex);
                result.add(MatrixUtils.mean(local));
                MatrixUtils.addInPlace(locals.get(postNeuronIndex), local);
            }
        }
        return result;
    }

    private static Result getSeparableInfo() {
        getSeparableInfo(value -> value > 0.0, "Positive");
        getSeparableInfo(value -> value < 0.0, "Negative");
        return getSeparableInfo(value -> true, null);
    }

    private static Result getSeparableInfo(DoublePredicate predicate, String subset) {
        Result result = new Result();
        for (int neuronIndex : ensemble.getBrain().getNeuronIndices(Brain.Layer.PROCESSING)) {
            result.add(Arrays.stream(locals.get(neuronIndex))
                    .map(value -> predicate.test(value) ? value : 0.0)
                    .average()
                    .getAsDouble());
        }
        print(Metric.SEPARABLE_INFO, subset, result);
        return result;
    }
}
