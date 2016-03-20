import java.util.*;

public class TimeSeries {
    private int dimension;
    private Collection<double[]> timeSeries;
    
    public TimeSeries(int dimension) {
        this.dimension = dimension;
        timeSeries = new LinkedList<double[]>();
    }
    
    public double[] get(int index) {
        double[] result = new double[timeSeries.size()];
        int time = 0;
        for (double[] values : timeSeries) {
            result[time] = values[index];
            time++;
        }
        return result;
    }
    
    public double[][] get(int[] indices) {
        double[][] result = new double[timeSeries.size()][indices.length];
        int time = 0;
        for (double[] values : timeSeries) {
            int resultIndex = 0;
            for (int valueIndex : indices) {
                result[time][resultIndex] = values[valueIndex];
                resultIndex++;
            }
            time++;
        }
        return result;
    }
    
    public void add(double[] values) {
        if (values.length != dimension) {
            throw new IllegalArgumentException(String.format("Number of values %d does not match dimension %d.", values.length, dimension));
        }
        timeSeries.add(values);
    }
}
