import java.io.*;
import java.util.*;

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
        Calculator calculator = new Calculator();
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(new InputStreamReader(System.in))) {
            reader.readArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                Collection<Integer> neuronIndices = ensemble.getBrain()
                        .getNeuronIndices(Brain.Layer.PROCESSING);
                double entropy = 0.0;
                for (int neuronIndex : neuronIndices) {
                    entropy += calculator.getEntropy(ensemble, neuronIndex);
                }
                System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), neuronIndices.size(), entropy);
            }
        }
    }
}
