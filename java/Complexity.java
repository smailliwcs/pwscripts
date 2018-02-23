import infodynamics.utils.*;

public class Complexity {
    public static void main(String[] args) throws Exception {
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(System.in)) {
            reader.readArguments(System.out);
            while (true) {
                TimeSeriesEnsemble ensemble = reader.read();
                if (ensemble == null) {
                    break;
                }
                int agentIndex = ensemble.getAgentIndex();
                int[] neuronIndices = ensemble.getProcessingNeuronIndices();
                double[] integrations = new double[ensemble.size()];
                double[] complexities = new double[ensemble.size()];
                for (int ensembleIndex = 0; ensembleIndex < ensemble.size(); ensembleIndex++) {
                    double[][] data = ensemble.get(ensembleIndex).getColumnsGaussian(neuronIndices, 1e-6);
                    double[][] covariance = MatrixUtils.covarianceMatrix(data);
                    double integration = getIntegration(covariance);
                    integrations[ensembleIndex] = integration;
                    complexities[ensembleIndex] = getComplexity(covariance, integration);
                }
                System.out.printf("%d I %g%n", agentIndex, MatrixUtils.mean(integrations));
                System.out.printf("%d C %g%n", agentIndex, MatrixUtils.mean(complexities));
            }
        }
    }
    
    private static double getIntegration(double[][] covariance) throws Exception {
        return Math.log(Utility.getDiagonalProduct(covariance) / MatrixUtils.determinantSymmPosDefMatrix(covariance)) / 2.0;
    }
    
    private static double getComplexity(double[][] covariance, double integration) throws Exception {
        double complexity = (covariance.length - 1) * integration;
        for (int index = 0; index < covariance.length; index++) {
            complexity -= getIntegration(MatrixUtils.copyMatrixEliminateRowAndColumn(covariance, index, index));
        }
        return complexity / covariance.length;
    }
}
