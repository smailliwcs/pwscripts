import java.util.*;

public class TimeSeries implements Iterable<double[]> {
    private static Random random;
    
    private int dimension;
    private Collection<double[]> data;
    
    static {
        random = new Random();
    }
    
    public TimeSeries(int dimension) {
        this.dimension = dimension;
        data = new LinkedList<double[]>();
    }
    
    public Iterator<double[]> iterator() {
        return data.iterator();
    }
    
    public double[] get(int index, double noise, boolean gaussianize) {
        Double[] noisyData = new Double[data.size()];
        int time = 0;
        for (double[] datum : data) {
            noisyData[time] = datum[index] + noise * random.nextGaussian();
            time++;
        }
        double[] results = new double[data.size()];
        if (gaussianize) {
            double[] gaussianData = new double[data.size()];
            for (time = 0; time < data.size(); time++) {
                gaussianData[time] = random.nextGaussian();
            }
            Arrays.sort(gaussianData);
            ArrayIndexComparator comparator = new ArrayIndexComparator(noisyData);
            Integer[] sortedTimes = comparator.getIndices();
            Arrays.sort(sortedTimes, comparator);
            time = 0;
            for (int sortedTime : sortedTimes) {
                results[sortedTime] = gaussianData[time];
                time++;
            }
        } else {
            for (time = 0; time < data.size(); time++) {
                results[time] = noisyData[time];
            }
        }
        return results;
    }
    
    public double[] get(int index, double noise) {
        return get(index, noise, false);
    }
    
    public double[] get(int index) {
        return get(index, 0.0, false);
    }
    
    public double[][] get(int[] indices, double noise, boolean gaussianize) {
        if (indices.length == 0) {
            return null;
        }
        double[][] results = new double[data.size()][indices.length];
        for (int index = 0; index < indices.length; index++) {
            int time = 0;
            for (double value : get(indices[index], noise, gaussianize)) {
                results[time][index] = value;
                time++;
            }
        }
        return results;
    }
    
    public double[][] get(int[] indices, double noise) {
        return get(indices, noise, false);
    }
    
    public double[][] get(int[] indices) {
        return get(indices, 0.0, false);
    }
    
    public void add(double[] datum) {
        if (datum.length != dimension) {
            throw new IllegalArgumentException(String.format("Number of values %d does not match dimension %d.", datum.length, dimension));
        }
        data.add(datum);
    }
}
