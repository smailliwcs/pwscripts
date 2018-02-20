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
                int[] neuronIndices = ensemble.getProcessingNeuronIndices();
                double[] integrations = new double[ensemble.size()];
                double[] complexities = new double[ensemble.size()];
                int index = 0;
                for (TimeSeries timeSeries : ensemble) {
                    double[][] data = timeSeries.getColumnsGaussian(neuronIndices, 1e-6);
                    double[][] covariance = MatrixUtils.covarianceMatrix(data);
                    double integration = getIntegration(covariance);
                    integrations[index] = integration;
                    complexities[index] = getComplexity(covariance, integration);
                    index++;
                }
                System.out.printf("%d I %g%n", ensemble.getAgentIndex(), MatrixUtils.mean(integrations));
                System.out.printf("%d C %g%n", ensemble.getAgentIndex(), MatrixUtils.mean(complexities));
            }
        }
    }
    
    private static double getIntegration(double[][] covariance) throws Exception {
        return Utility.log2(getDiagonalProduct(covariance) / MatrixUtils.determinantSymmPosDefMatrix(covariance)) / 2.0;
    }
    
    private static double getDiagonalProduct(double[][] matrix) {
        double product = 1.0;
        for (int index = 0; index < matrix.length; index++) {
            product *= matrix[index][index];
        }
        return product;
    }
    
    private static double getComplexity(double[][] covariance, double integration) throws Exception {
        double complexity = (covariance.length - 1) * integration;
        for (int index = 0; index < covariance.length; index++) {
            complexity -= getIntegration(MatrixUtils.copyMatrixEliminateRowAndColumn(covariance, index, index));
        }
        return complexity / covariance.length;
    }
}
