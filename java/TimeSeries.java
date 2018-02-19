import java.util.*;

public class TimeSeries extends ArrayList<double[]> {
    private static Random random;
    
    static {
        random = new Random();
    }
    
    private int dimension;
    
    public TimeSeries(int dimension, int capacity) {
        super(capacity);
        this.dimension = dimension;
    }
    
    public TimeSeries(int dimension) {
        this(dimension, 100);
    }
    
    public double[][] getColumns(int[] indices) {
        double[][] columns = new double[size()][indices.length];
        for (int time = 0; time < size(); time++) {
            double[] source = get(time);
            double[] target = columns[time];
            for (int index = 0; index < indices.length; index++) {
                target[index] = source[indices[index]];
            }
        }
        return columns;
    }
    
    private void getColumnGaussian(int index, double noise, double[] gaussians, double[] column) {
        for (int time = 0; time < size(); time++) {
            gaussians[time] = random.nextGaussian();
            column[time] = get(time)[index] + noise * random.nextGaussian();
        }
        Arrays.sort(gaussians);
        IndexComparator comparator = new IndexComparator(column);
        Integer[] times = comparator.getIndices();
        Arrays.sort(times, comparator);
        for (int order = 0; order < size(); order++) {
            column[times[order]] = gaussians[order];
        }
    }
    
    public double[][] getColumnsGaussian(int[] indices, double noise) {
        double[] gaussians = new double[size()];
        double[] column = new double[size()];
        double[][] columns = new double[size()][indices.length];
        for (int index = 0; index < indices.length; index++) {
            getColumnGaussian(indices[index], noise, gaussians, column);
            for (int time = 0; time < size(); time++) {
                columns[time][index] = column[time];
            }
        }
        return columns;
    }
    
    public int[] getColumnDiscrete(int index, int base) {
        int[] column = new int[size()];
        for (int time = 0; time < size(); time++) {
            int value = (int)(get(time)[index] * base);
            if (value == base) {
                value--;
            }
            column[time] = value;
        }
        return column;
    }
    
    public boolean add(double[] row) {
        if (row.length != dimension) {
            throw new IllegalArgumentException(String.format("Row length %d does not match dimension %d.", row.length, dimension));
        }
        return super.add(row);
    }
}
