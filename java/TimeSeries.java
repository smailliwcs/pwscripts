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
    
    public double[] getColumn(int index, Double noise, boolean gaussianize) {
        double[] column = new double[size()];
        for (int time = 0; time < size(); time++) {
            column[time] = get(time)[index];
        }
        if (noise != null) {
            for (int time = 0; time < size(); time++) {
                column[time] += noise * random.nextGaussian();
            }
        }
        if (gaussianize) {
            double[] gaussians = new double[size()];
            for (int time = 0; time < size(); time++) {
                gaussians[time] = random.nextGaussian();
            }
            Arrays.sort(gaussians);
            IndexComparator comparator = new IndexComparator(column);
            Integer[] sortedTimes = comparator.getIndices();
            Arrays.sort(sortedTimes, comparator);
            for (int time = 0; time < size(); time++) {
                column[sortedTimes[time]] = gaussians[time];
            }
        }
        return column;
    }
    
    public double[] getColumn(int index) {
        return getColumn(index, null, false);
    }
    
    public double[][] getColumns(int[] indices, Double noise, boolean gaussianize) {
        double[][] columns = new double[size()][indices.length];
        for (int index = 0; index < indices.length; index++) {
            double[] column = getColumn(indices[index], noise, gaussianize);
            for (int time = 0; time < size(); time++) {
                columns[time][index] = column[time];
            }
        }
        return columns;
    }
    
    public double[][] getColumns(int[] indices) {
        return getColumns(indices, null, false);
    }
    
    public boolean add(double[] row) {
        if (row.length != dimension) {
            throw new IllegalArgumentException(String.format("Row length %d does not match dimension %d.", row.length, dimension));
        }
        return super.add(row);
    }
}
