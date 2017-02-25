import infodynamics.utils.*;
import java.util.*;

public class Complexity {
    public static void main(String[] args) throws Exception {
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.printArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                double noise = 1e-6;
                do {
                    try {
                        int[] processingNeuronIndices = ensemble.getProcessingNeuronIndices();
                        double[][] data = ensemble.getCombinedTimeSeries().get(processingNeuronIndices, noise, true);
                        double[][] covariance = MatrixUtils.covarianceMatrix(data);
                        double determinant = MatrixUtils.determinantSymmPosDefMatrix(covariance);
                        double complexity = (processingNeuronIndices.length - 1) * getIntegration(covariance, determinant);
                        for (int index = 0; index < processingNeuronIndices.length; index++) {
                            int[] otherIndices = getOtherIndices(processingNeuronIndices.length, index);
                            double[][] subcovariance = MatrixUtils.selectRowsAndColumns(covariance, otherIndices, otherIndices);
                            double subdeterminant = MatrixUtils.determinantSymmPosDefMatrix(subcovariance);
                            complexity -= getIntegration(subcovariance, subdeterminant);
                        }
                        complexity /= processingNeuronIndices.length;
                        System.out.printf("%d %g%n", ensemble.getAgentIndex(), complexity);
                        break;
                    } catch (Exception ex) {
                        System.err.printf("%d: %s%n", ensemble.getAgentIndex(), ex.getMessage());
                        System.err.println("Increasing noise...");
                        noise *= 10.0;
                    }
                } while (noise < 1.0 - 1e-6);
            }
        }
    }
    
    private static double getIntegration(double[][] covariance, double determinant) throws Exception {
        double varianceLogSum = 0.0;
        for (int index = 0; index < covariance.length; index++) {
            varianceLogSum += Math.log(covariance[index][index]);
        }
        return 0.5 * (varianceLogSum - Math.log(determinant));
    }
    
    private static int[] getOtherIndices(int count, int index) {
        Collection<Integer> otherIndices = new LinkedList<Integer>();
        for (int otherIndex = 0; otherIndex < count; otherIndex++) {
            if (otherIndex == index) {
                continue;
            }
            otherIndices.add(otherIndex);
        }
        return Utility.toPrimitive(otherIndices);
    }
}
