import java.io.*;
import java.util.*;

import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class CompleteTransferEntropy {
    private static class Calculator extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
        private int embeddingLength;

        public Calculator(boolean useGpu, int embeddingLength) {
            setProperty(PROP_USE_GPU, Boolean.toString(useGpu));
            this.embeddingLength = embeddingLength;
        }

        public double getCompleteTransferEntropy(TimeSeriesEnsemble ensemble, int preNeuronIndex, int postNeuronIndex)
                throws Exception {
            Collection<Integer> conditionalNeuronIndices = ensemble.getBrain().getPreNeuronIndices(postNeuronIndex);
            conditionalNeuronIndices.remove(preNeuronIndex);
            initialise(1, 1, embeddingLength + conditionalNeuronIndices.size());
            startAddObservations();
            for (TimeSeries observations : ensemble) {
                int count = observations.size() - embeddingLength;
                double[][] conditionalObservations = MatrixUtils.appendColumns(
                        observations.embed(postNeuronIndex, embeddingLength, 0, count),
                        observations.slice(conditionalNeuronIndices, embeddingLength - 1, count));
                addObservations(
                        observations.slice(preNeuronIndex, embeddingLength - 1, count),
                        observations.slice(postNeuronIndex, embeddingLength, count),
                        conditionalObservations);
            }
            finaliseAddObservations();
            return computeAverageLocalOfObservations();
        }
    }

    private static class Arguments {
        public static Arguments parse(String[] args) {
            try (ArgumentParser parser = new ArgumentParser(
                    args,
                    CollectiveTransferEntropy.class.getName(),
                    "GPU",
                    "EMBEDDING",
                    "SYNAPSES")) {
                boolean useGpu = parser.parse(Boolean::parseBoolean);
                int embeddingLength = parser.parse(
                        Integer::parseInt,
                        argument -> argument >= 1,
                        "Invalid embedding length");
                int synapseCountMax = parser.parse(
                        Integer::parseInt,
                        argument -> argument >= 1,
                        "Invalid maximum number of synapses");
                return new Arguments(useGpu, embeddingLength, synapseCountMax);
            }
        }

        public final boolean useGpu;
        public final int embeddingLength;
        public final int synapseCountMax;

        private Arguments(boolean useGpu, int embeddingLength, int synapseCountMax) {
            this.useGpu = useGpu;
            this.embeddingLength = embeddingLength;
            this.synapseCountMax = synapseCountMax;
        }

        public String toString() {
            StringBuilder result = new StringBuilder();
            result.append(String.format("# EMBEDDING = %d%n", embeddingLength));
            result.append(String.format("# SYNAPSES = %d%n", synapseCountMax));
            return result.toString();
        }
    }

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(args);
        Calculator calculator = new Calculator(arguments.useGpu, arguments.embeddingLength);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(new InputStreamReader(System.in))) {
            reader.readArguments(System.out);
            System.out.print(arguments);
            System.out.println("agent count value");
            while (true) {
                TimeSeriesEnsemble ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                List<Synapse> synapses = new ArrayList<Synapse>(ensemble.getBrain().getSynapses());
                if (synapses.size() > arguments.synapseCountMax) {
                    Collections.shuffle(synapses);
                }
                Result result = new Result();
                for (Synapse synapse : synapses) {
                    result.add(calculator.getCompleteTransferEntropy(
                            ensemble,
                            synapse.getPreNeuronIndex(),
                            synapse.getPostNeuronIndex()));
                    if (result.getCount() == arguments.synapseCountMax) {
                        break;
                    }
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentId(), result.getCount(), result.getSum());
            }
        }
    }
}
