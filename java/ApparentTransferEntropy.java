import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import java.util.*;

public class ApparentTransferEntropy {
    private static TransferEntropyCalculator calculator;
    private static Properties properties;
    
    public static void main(String[] args) throws Exception {
        calculator = new TransferEntropyCalculatorKraskov();
        properties = Utility.setProperties(calculator);
        Utility.printProperties(properties, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                if (ensemble.getSynapses().isEmpty()) {
                    System.out.printf("%d - - 0%n", ensemble.getAgentIndex());
                } else {
                    for (Synapse synapse : ensemble.getSynapses()) {
                        System.out.printf(
                            "%d %d %d %g%n",
                            ensemble.getAgentIndex(),
                            synapse.getPreNeuronIndex(),
                            synapse.getPostNeuronIndex(),
                            calculate(ensemble, synapse));
                    }
                }
            }
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble, Synapse synapse) throws Exception {
        calculator.initialise();
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            double[] source = timeSeries.get(synapse.getPreNeuronIndex());
            double[] target = timeSeries.get(synapse.getPostNeuronIndex());
            calculator.addObservations(source, target);
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
}
