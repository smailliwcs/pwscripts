import java.util.*;

public class Utility {
    public static double getMean(Iterable<Double> values) {
        int count = 0;
        double sum = 0.0;
        for (double value : values) {
            count++;
            sum += value;
        }
        return sum / count;
    }
}
