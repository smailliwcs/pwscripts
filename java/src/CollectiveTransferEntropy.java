import java.io.*;
import java.util.*;

import infodynamics.measures.continuous.kraskov.*;

public class CollectiveTransferEntropy {
    private static class Calculator extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
        private int embeddingLength;

        public Calculator(boolean useGpu, int embeddingLength) {
            setProperty(PROP_USE_GPU, Boolean.toString(useGpu));
            this.embeddingLength = embeddingLength;
        }

        public double getCollectiveTransferEntropy(TimeSeriesEnsemble ensemble, int postNeuronIndex) throws Exception {
            Collection<Integer> preNeuronIndices = ensemble.getBrain().getPreNeuronIndices(postNeuronIndex);
            if (preNeuronIndices.size() == 0) {
                return 0.0;
            }
            initialise(preNeuronIndices.size(), 1, embeddingLength);
            startAddObservations();
            for (TimeSeries observations : ensemble) {
                int count = observations.size() - embeddingLength;
                addObservations(
                        observations.slice(preNeuronIndices, embeddingLength - 1, count),
                        observations.slice(postNeuronIndex, embeddingLength, count),
                        observations.embed(postNeuronIndex, embeddingLength, 0, count));
            }
            finaliseAddObservations();
            return computeAverageLocalOfObservations();
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
            try (ArgumentParser parser = new ArgumentParser(
                    getUsage(),
                    CollectiveTransferEntropy.class.getName(),
                    args)) {
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

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(args);
        Calculator calculator = new Calculator(arguments.useGpu, arguments.embeddingLength);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.print(arguments);
            System.out.println("agent count value");
            while (true) {
                TimeSeriesEnsemble ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                Result result = new Result();
                for (int neuronIndex : ensemble.getBrain().getNeuronIndices(Brain.Layer.PROCESSING)) {
                    result.add(calculator.getCollectiveTransferEntropy(ensemble, neuronIndex));
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentId(), result.getCount(), result.getSum());
            }
        }
    }
}
