import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import java.util.*;

public class Complexity {
    private static boolean complexityOnly;
    private static MutualInfoCalculatorMultiVariate mutualInfoCalculator;
    private static MultiInfoCalculator integrationCalculator;
    
    public static void main(String[] args) throws Exception {
        parseArgs(args);
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
                double complexity = 0.0;
                int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
                for (int neuronIndex : processingNeuronIndices) {
                    int[] otherNeuronIndices = getOtherNeuronIndices(processingNeuronIndices, neuronIndex);
                    double mutualInfo = calculateMutualInfo(ensemble, new int[] { neuronIndex }, otherNeuronIndices);
                    if (complexityOnly) {
                        complexity += mutualInfo;
                    } else {
                        System.out.printf("%d %d %g%n", ensemble.getAgentIndex(), neuronIndex, mutualInfo);
                    }
                }
                double integration = calculateIntegration(ensemble, processingNeuronIndices);
                if (complexityOnly) {
                    complexity -= integration;
                    System.out.printf("%d %g%n", ensemble.getAgentIndex(), complexity);
                } else {
                    System.out.printf("%d - %g%n", ensemble.getAgentIndex(), integration);
                }
            }
        }
    }
    
    private static void parseArgs(String[] args) {
        if (args.length == 1) {
            if (args[0].equals("--complexity-only")) {
                complexityOnly = true;
            } else {
                throw new IllegalArgumentException();
            }
        } else if (args.length > 1) {
            throw new IllegalArgumentException();
        }
    }
    
    private static double calculateMutualInfo(TimeSeriesEnsemble ensemble, int[] neuronIndices1, int[] neuronIndices2) throws Exception {
        mutualInfoCalculator.initialise(neuronIndices1.length, neuronIndices2.length);
        mutualInfoCalculator.startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            double[][] data1 = timeSeries.get(neuronIndices1);
            double[][] data2 = timeSeries.get(neuronIndices2);
            mutualInfoCalculator.addObservations(data1, data2);
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
