import infodynamics.measures.continuous.kraskov.*;
import java.util.*;

public class ApparentTransferEntropy {
    public static void main(String[] args) throws Exception {
        TransferEntropyCalculatorKraskov calculator = new TransferEntropyCalculatorKraskov();
        Utility.setProperties(calculator);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                Collection<Double> results = new LinkedList<Double>();
                for (Synapse synapse : ensemble.getSynapses()) {
                    calculator.initialise();
                    calculator.startAddObservations();
                    for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
                        double[] source = timeSeries.get(synapse.getPreNeuronIndex());
                        double[] target = timeSeries.get(synapse.getPostNeuronIndex());
                        calculator.addObservations(source, target);
                    }
                    calculator.finaliseAddObservations();
                    results.add(calculator.computeAverageLocalOfObservations());
                }
                double result = results.isEmpty() ? 0.0 : Utility.getSum(results);
                System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), ensemble.getSynapses().size(), result);
            }
        }
    }
}
