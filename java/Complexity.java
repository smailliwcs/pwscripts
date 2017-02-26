import infodynamics.utils.*;
import java.util.*;

public class Complexity {
    public static void main(String[] args) throws Exception {
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                try {
                    int[] neuronIndices = ensemble.getProcessingNeuronIndices();
                    double[][] data = ensemble.combine().getColumns(neuronIndices, 1e-6, true);
                    double[][] covariance = MatrixUtils.covarianceMatrix(data);
                    double determinant = MatrixUtils.determinantSymmPosDefMatrix(covariance);
                    double integration = getIntegration(covariance, determinant);
                    double complexity = (neuronIndices.length - 1) * integration;
                    for (int index = 0; index < neuronIndices.length; index++) {
                        int[] otherIndices = getOtherIndices(neuronIndices.length, index);
                        double[][] subcovariance = MatrixUtils.selectRowsAndColumns(covariance, otherIndices, otherIndices);
                        double subdeterminant = MatrixUtils.determinantSymmPosDefMatrix(subcovariance);
                        complexity -= getIntegration(subcovariance, subdeterminant);
                    }
                    complexity /= neuronIndices.length;
                    System.out.printf("%d I %g%n", ensemble.getAgentIndex(), integration);
                    System.out.printf("%d C %g%n", ensemble.getAgentIndex(), complexity);
                } catch (Exception ex) {
                    System.err.printf("%d: %s%n", ensemble.getAgentIndex(), ex.getMessage());
                }
            }
        }
    }
    
    private static double getIntegration(double[][] covariance, double determinant) {
        double varianceLogSum = 0.0;
        for (int index = 0; index < covariance.length; index++) {
            varianceLogSum += Math.log(covariance[index][index]);
        }
        return 0.5 * (varianceLogSum - Math.log(determinant));
    }
    
    private static int[] getOtherIndices(int count, int index) {
        if (index < 0 || index >= count) {
            throw new IllegalArgumentException(String.format("Index %d is not in acceptable range [0, %d].", index, count - 1));
        }
        int[] otherIndices = new int[count - 1];
        for (int otherIndex = 0; otherIndex < count; otherIndex++) {
            if (otherIndex < index) {
                otherIndices[otherIndex] = otherIndex;
            } else if (otherIndex > index) {
                otherIndices[otherIndex - 1] = otherIndex;
            }
        }
        return otherIndices;
    }
}
