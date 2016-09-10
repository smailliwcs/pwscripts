import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import java.util.*;

public class Complexity {
    private static MutualInfoCalculatorMultiVariate mutualInfoCalculator;
    private static MultiInfoCalculator integrationCalculator;
    
    public static void main(String[] args) throws Exception {
        mutualInfoCalculator = new MutualInfoCalculatorMultiVariateKraskov1();
        integrationCalculator = new MultiInfoCalculatorKraskov1();
        Utility.setProperties(mutualInfoCalculator, System.out);
        Utility.setProperties(integrationCalculator, System.out);
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                System.out.printf("%d %g%n", ensemble.getAgentIndex(), calculate(ensemble));
            }
        }
    }
    
    private static double calculate(TimeSeriesEnsemble ensemble) throws Exception {
        int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
        double result = 0.0;
        for (int neuronIndex : processingNeuronIndices) {
            int[] otherNeuronIndices = getOtherNeuronIndices(processingNeuronIndices, neuronIndex);
            result += calculateMutualInfo(ensemble, new int[] { neuronIndex }, otherNeuronIndices);
        }
        result -= calculateIntegration(ensemble, processingNeuronIndices);
        return result;
    }
    
    private static double calculateMutualInfo(TimeSeriesEnsemble ensemble, int[] sourceNeuronIndices, int[] targetNeuronIndices) throws Exception {
        mutualInfoCalculator.initialise(sourceNeuronIndices.length, targetNeuronIndices.length);
        mutualInfoCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            double[][] source = timeSeries.get(sourceNeuronIndices);
            double[][] target = timeSeries.get(targetNeuronIndices);
            mutualInfoCalculator.addObservations(source, target);
        }
        mutualInfoCalculator.finaliseAddObservations();
        return mutualInfoCalculator.computeAverageLocalOfObservations();
    }
    
    private static double calculateIntegration(TimeSeriesEnsemble ensemble, int[] neuronIndices) throws Exception {
        integrationCalculator.initialise(neuronIndices.length);
        integrationCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            integrationCalculator.addObservations(timeSeries.get(neuronIndices));
        }
        integrationCalculator.finaliseAddObservations();
        return integrationCalculator.computeAverageLocalOfObservations();
    }
    
    private static int[] getOtherNeuronIndices(int[] neuronIndices, int neuronIndex) {
        Collection<Integer> otherNeuronIndices = new LinkedList<Integer>();
        for (int otherNeuronIndex : neuronIndices) {
            if (otherNeuronIndex == neuronIndex) {
                continue;
            }
            otherNeuronIndices.add(otherNeuronIndex);
        }
        return Utility.toPrimitive(otherNeuronIndices);
    }
}
