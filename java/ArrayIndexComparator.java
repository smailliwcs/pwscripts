import java.util.*;

public class ArrayIndexComparator implements Comparator<Integer> {
    private Double[] array;
    
    public ArrayIndexComparator(Double[] array) {
        this.array = array;
    }
    
    public Integer[] getIndices() {
        Integer[] indices = new Integer[array.length];
        for (int index = 0; index < array.length; index++) {
            indices[index] = index;
        }
        return indices;
    }
    
    public int compare(Integer index1, Integer index2) {
        return array[index1].compareTo(array[index2]);
    }
}
