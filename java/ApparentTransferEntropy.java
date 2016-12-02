import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;

public class ApparentTransferEntropy {
    private static TransferEntropyCalculator calculator;
    
    public static void main(String[] args) throws Exception {
        calculator = new TransferEntropyCalculatorKraskov();
        Utility.setProperties(calculator, System.out);
        parseArgs(args);
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
    
    private static void parseArgs(String[] args) throws Exception  {
        if (args.length != 2) {
            throw new IllegalArgumentException();
        }
        calculator.setProperty(calculator.L_PROP_NAME, args[0]);
        System.out.printf("# %s = %s%n", calculator.L_PROP_NAME, args[0]);
        calculator.setProperty(calculator.K_PROP_NAME, args[1]);
        System.out.printf("# %s = %s%n", calculator.K_PROP_NAME, args[1]);
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
