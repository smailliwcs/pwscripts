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
        public static Arguments parse(Queue<String> args) {
            try {
                boolean useGpu = false;
                while (!args.isEmpty() && args.peek().startsWith("--")) {
                    switch (args.remove()) {
                    case "--use-gpu":
                        useGpu = true;
                        break;
                    default:
                        assert false;
                    }
                }
                int embeddingLength = Integer.parseInt(args.remove());
                assert args.isEmpty();
                return new Arguments(useGpu, embeddingLength);
            } catch (Throwable e) {
                printUsage(System.err);
                System.exit(1);
                return null;
            }
        }

        public static void printUsage(PrintStream out) {
            out.printf("Usage: %s [--use-gpu] EMBEDDING_LENGTH%n", InfoDynamics.class.getSimpleName());
        }

        public final boolean useGpu;
        public final int embeddingLength;

        private Arguments(boolean useGpu, int embeddingLength) {
            this.useGpu = useGpu;
            this.embeddingLength = embeddingLength;
        }

        public void print(PrintStream out) {
            out.printf("# embeddingLength = %d%n", embeddingLength);
        }
    }

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(new LinkedList<String>(Arrays.asList(args)));
        Calculator calculator = new Calculator(arguments.useGpu, arguments.embeddingLength);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(new InputStreamReader(System.in))) {
            reader.readArguments(System.out);
            arguments.print(System.out);
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
