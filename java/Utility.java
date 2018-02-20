import java.util.*;

public class Utility {
    public static int[] getRange(int start, int count) {
        int[] range = new int[count];
        for (int index = 0; index < count; index++) {
            range[index] = start + index;
        }
        return range;
    }
    
    public static double log2(double x) {
        return Math.log(x) / Math.log(2.0);
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
