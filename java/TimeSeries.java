import java.util.*;

public class TimeSeries implements Iterable<double[]> {
    private int dimension;
    private Collection<double[]> data;
    
    public TimeSeries(int dimension) {
        this.dimension = dimension;
        data = new LinkedList<double[]>();
    }
    
    public Iterator<double[]> iterator() {
        return data.iterator();
    }
    
    public double[] get(int index) {
        double[] results = new double[data.size()];
        int time = 0;
        for (double[] datum : data) {
            results[time] = datum[index];
            time++;
        }
        return results;
    }
    
    public double[][] get(int[] indices) {
        if (indices.length == 0) {
            return null;
        }
        double[][] results = new double[data.size()][indices.length];
        int time = 0;
        for (double[] datum : data) {
            double[] result = results[time];
            for (int index = 0; index < indices.length; index++) {
                result[index] = datum[indices[index]];
            }
            time++;
        }
        return results;
    }
    
    public void add(double[] datum) {
        if (datum.length != dimension) {
            throw new IllegalArgumentException(String.format("Number of values %d does not match dimension %d.", datum.length, dimension));
        }
        data.add(datum);
    }
}
