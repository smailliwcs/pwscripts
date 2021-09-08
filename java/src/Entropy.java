import java.io.*;

import infodynamics.measures.continuous.kozachenko.*;

public class Entropy {
    private static class Calculator extends EntropyCalculatorMultiVariateKozachenko {
        public double getEntropy(TimeSeriesEnsemble ensemble, int neuronIndex) throws Exception {
            initialise(1);
            startAddObservations();
            for (TimeSeries observations : ensemble) {
                addObservations(observations.slice(neuronIndex));
            }
            finaliseAddObservations();
            return computeAverageLocalOfObservations();
        }
    }

    private static String getUsage() {
        StringBuilder usage = new StringBuilder();
        usage.append("Usage: %s%n");
        return usage.toString();
    }

    public static void main(String[] args) throws Exception {
        try (ArgumentParser parser = new ArgumentParser(getUsage(), Entropy.class.getName(), args)) {
        }
        Calculator calculator = new Calculator();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            System.out.println("agent count value");
            while (true) {
                TimeSeriesEnsemble ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                Result result = new Result();
                for (int neuronIndex : ensemble.getBrain().getNeuronIndices(Brain.Layer.PROCESSING)) {
                    result.add(calculator.getEntropy(ensemble, neuronIndex));
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentId(), result.getCount(), result.getSum());
            }
        }
    }
}
