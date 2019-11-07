import java.util.*;
import java.util.stream.*;

@SuppressWarnings("serial")
public class TimeSeries extends LinkedList<List<Double>> {
    private int dimension;

    public TimeSeries(int dimension) {
        this.dimension = dimension;
    }

    public int getDimension() {
        return dimension;
    }

    public boolean add(List<Double> observation) {
        assert observation.size() == dimension;
        return super.add(observation);
    }

    private static double[] slice(List<Double> observation, Collection<Integer> variables) {
        return variables.stream()
                .mapToDouble(variable -> observation.get(variable))
                .toArray();
    }

    public double[][] slice(Collection<Integer> variables) {
        return stream().map(observation -> slice(observation, variables))
                .toArray(double[][]::new);
    }

    public double[][] slice(int variable) {
        return slice(
                IntStream.of(variable)
                        .boxed()
                        .collect(Collectors.toList()));
    }
}
