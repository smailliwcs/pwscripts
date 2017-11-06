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
                    double integration = getIntegration(covariance);
                    System.out.printf("%d I %g%n", ensemble.getAgentIndex(), integration);
                    double complexity = (neuronIndices.length - 1) * integration;
                    for (int index = 0; index < neuronIndices.length; index++) {
                        complexity -= getIntegration(MatrixUtils.copyMatrixEliminateRowAndColumn(covariance, index, index));
                    }
                    complexity /= neuronIndices.length;
                    System.out.printf("%d C %g%n", ensemble.getAgentIndex(), complexity);
                } catch (Exception ex) {
                    System.err.printf("%d: %s%n", ensemble.getAgentIndex(), ex.getMessage());
                }
            }
        }
    }
    
    private static double getIntegration(double[][] covariance) throws Exception {
        return Math.log(getDiagonalProduct(covariance) / MatrixUtils.determinantSymmPosDefMatrix(covariance)) / 2.0;
    }
    
    private static double getDiagonalProduct(double[][] matrix) {
        double product = 1.0;
        for (int index = 0; index < matrix.length; index++) {
            product *= matrix[index][index];
        }
        return product;
    }
}
