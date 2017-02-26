import java.util.*;

public class IndexComparator implements Comparator<Integer> {
    private double[] values;
    
    public IndexComparator(double[] values) {
        this.values = values;
    }
    
    public Integer[] getIndices() {
        Integer[] indices = new Integer[values.length];
        for (int index = 0; index < values.length; index++) {
            indices[index] = index;
        }
        return indices;
    }
    
    public int compare(Integer index1, Integer index2) {
        return Double.compare(values[index1], values[index2]);
    }
}
