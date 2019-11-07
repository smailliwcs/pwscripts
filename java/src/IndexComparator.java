import java.util.*;

public class IndexComparator implements Comparator<Integer> {
    private double[] values;

    public IndexComparator(double[] values) {
        this.values = values;
    }

    public int compare(Integer index1, Integer index2) {
        return Double.compare(values[index1], values[index2]);
    }
}
