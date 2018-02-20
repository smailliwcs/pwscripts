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
}
