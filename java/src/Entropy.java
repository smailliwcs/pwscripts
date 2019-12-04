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

    public static void main(String[] args) throws Exception {
        assert args.length == 0;
        Calculator calculator = new Calculator();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(new InputStreamReader(System.in))) {
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
