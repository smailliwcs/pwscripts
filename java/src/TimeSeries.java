import java.util.*;
import java.util.stream.*;

@SuppressWarnings("serial")
public class TimeSeries extends LinkedList<List<Double>> {
    private static double[] slice(List<Double> observation, Collection<Integer> variables) {
        return variables.stream()
                .mapToDouble(observation::get)
                .toArray();
    }

    private static double[] embed(Collection<Iterator<List<Double>>> embeddings, Collection<Integer> variables) {
        return embeddings.stream()
                .map(Iterator<List<Double>>::next)
                .flatMapToDouble(observation -> variables.stream().mapToDouble(observation::get))
                .toArray();
    }

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

    public double[][] slice(Collection<Integer> variables, int startIndex, int count) {
        return stream()
                .skip(startIndex)
                .limit(count)
                .map(observation -> slice(observation, variables))
                .toArray(double[][]::new);
    }

    public double[][] slice(Collection<Integer> variables) {
        return slice(variables, 0, size());
    }

    public double[][] slice(int variable, int startIndex, int count) {
        return slice(Arrays.asList(variable), startIndex, count);
    }

    public double[][] slice(int variable) {
        return slice(variable, 0, size());
    }

    public double[][] embed(Collection<Integer> variables, int embeddingLength, int startIndex, int count) {
        Collection<Iterator<List<Double>>> embeddings = IntStream.range(0, embeddingLength)
                .mapToObj(embeddingIndex -> stream().skip(startIndex + embeddingIndex).iterator())
                .collect(Collectors.toList());
        return Stream.generate(() -> embed(embeddings, variables))
                .limit(count)
                .toArray(double[][]::new);
    }

    public double[][] embed(int variable, int embeddingLength, int startIndex, int count) {
        return embed(Arrays.asList(variable), embeddingLength, startIndex, count);
    }
}
