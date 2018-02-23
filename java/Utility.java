import java.util.*;

public class Utility {
    public static double getDiagonalProduct(double[][] matrix) {
        double product = 1.0;
        for (int index = 0; index < matrix.length; index++) {
            product *= matrix[index][index];
        }
        return product;
    }
    
    public static int[] getRange(int start, int count) {
        int[] range = new int[count];
        for (int index = 0; index < count; index++) {
            range[index] = start + index;
        }
        return range;
    }
    
    public static double log(double x, double base) {
        return Math.log(x) / Math.log(base);
    }
    
    public static double log2(double x) {
        return log(x, 2.0);
    }
    
    public static int[] toPrimitive(Collection<Integer> values) {
        int[] result = new int[values.size()];
        int index = 0;
        for (int value : values) {
            result[index] = value;
            index++;
        }
        return result;
    }
}
