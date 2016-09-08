import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;
import java.util.*;

public class CompleteTransferEntropy {
    private static ConditionalTransferEntropyCalculator calculator;
    private static Properties properties;
    
    public static void main(String[] args) throws Exception {
        calculator = new ConditionalTransferEntropyCalculatorKraskov();
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
        int[] conditionalNeuronIndices = getConditionalNeuronIndices(ensemble.getSynapses(), synapse);
        setConditionalProperties(conditionalNeuronIndices.length);
        calculator.initialise();
        calculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            double[] source = timeSeries.get(synapse.getPreNeuronIndex());
            double[] target = timeSeries.get(synapse.getPostNeuronIndex());
            double[][] conditionals = timeSeries.get(conditionalNeuronIndices);
            calculator.addObservations(source, target, conditionals);
        }
        calculator.finaliseAddObservations();
        return calculator.computeAverageLocalOfObservations();
    }
    
    private static int[] getConditionalNeuronIndices(Collection<Synapse> synapses, Synapse synapse) {
        Collection<Integer> conditionalNeuronIndices = new LinkedList<Integer>();
        for (Synapse conditionalSynapse : synapses) {
            if (conditionalSynapse.getPostNeuronIndex() != synapse.getPostNeuronIndex()) {
                continue;
            }
            if (conditionalSynapse.getPreNeuronIndex() == synapse.getPreNeuronIndex()) {
                continue;
            }
            conditionalNeuronIndices.add(conditionalSynapse.getPreNeuronIndex());
        }
        return Utility.toPrimitive(conditionalNeuronIndices);
    }
    
    private static void setConditionalProperties(int dimension) throws Exception {
        setConditionalProperty(ConditionalTransferEntropyCalculator.COND_EMBED_LENGTHS_PROP_NAME, dimension);
        setConditionalProperty(ConditionalTransferEntropyCalculator.COND_EMBED_DELAYS_PROP_NAME, dimension);
        setConditionalProperty(ConditionalTransferEntropyCalculator.COND_DELAYS_PROP_NAME, dimension);
    }
    
    private static void setConditionalProperty(String key, int dimension) throws Exception {
        int value;
        if (properties == null) {
            value = 1;
        } else {
            value = Integer.parseInt(properties.getProperty(key));
        }
        int[] values = new int[dimension];
        Arrays.fill(values, value);
        calculator.setProperty(key, MatrixUtils.arrayToString(values));
    }
}
