import java.io.*;
import java.util.*;

import infodynamics.utils.*;

public class Complexity {
    private static class Calculator {
        private static final double NOISE = 1e-6;

        public static void gaussianize(double[][] observations, int dimension) {
            Random random = new Random();
            Integer[] times = new Integer[observations.length];
            double[] values = new double[observations.length];
            double[] gaussians = new double[observations.length];
            for (int variable = 0; variable < dimension; variable++) {
                for (int time = 0; time < observations.length; time++) {
                    times[time] = time;
                    values[time] = observations[time][variable] + random.nextGaussian() * NOISE;
                    gaussians[time] = random.nextGaussian();
                }
                Arrays.sort(times, new IndexComparator(values));
                Arrays.sort(gaussians);
                for (int rank = 0; rank < observations.length; rank++) {
                    observations[times[rank]][variable] = gaussians[rank];
                }
            }
        }

        private static double getDiagonalProduct(double[][] matrix) {
            double product = 1.0;
            for (int index = 0; index < matrix.length; index++) {
                product *= matrix[index][index];
            }
            return product;
        }

        private static double[][] getSubset(double[][] matrix, int index) {
            return MatrixUtils.copyMatrixEliminateRowAndColumn(matrix, index, index);
        }

        public static double getIntegration(double[][] covariance) throws Exception {
            return 0.5 * Math.log(getDiagonalProduct(covariance) / MatrixUtils.determinantSymmPosDefMatrix(covariance));
        }

        public static double getComplexity(double[][] covariance, double integration) throws Exception {
            double subsetIntegration = 0.0;
            for (int index = 0; index < covariance.length; index++) {
                subsetIntegration += getIntegration(getSubset(covariance, index));
            }
            return ((covariance.length - 1) * integration - subsetIntegration) / covariance.length;
        }
    }

    public static void main(String[] args) throws Exception {
        assert args.length == 0;
        try (TimeSeriesEnsembleReader reader = new TimeSeriesEnsembleReader(new InputStreamReader(System.in))) {
            reader.readArguments(System.out);
            System.out.println("agent count integration complexity");
            while (true) {
                TimeSeriesEnsemble ensemble = reader.readTimeSeriesEnsemble();
                if (ensemble == null) {
                    break;
                }
                Collection<Integer> neuronIndices = ensemble.getBrain().getNeuronIndices(Brain.Layer.PROCESSING);
                double[][] observations = ensemble.concatenate().slice(neuronIndices);
                Calculator.gaussianize(observations, neuronIndices.size());
                double[][] covariance = MatrixUtils.covarianceMatrix(observations);
                double integration = Calculator.getIntegration(covariance);
                double complexity = Calculator.getComplexity(covariance, integration);
                System.out.printf(
                        "%d %d %g %g%n",
                        ensemble.getAgentId(),
                        neuronIndices.size(),
                        integration,
                        complexity);
            }
        }
    }
}
