import infodynamics.measures.continuous.*;
import java.io.*;
import java.util.*;

public class Utility {
    public static void printProperties(Properties properties, PrintStream out) {
        for (String key : properties.stringPropertyNames()) {
            out.printf("# %s = %s%n", key, properties.getProperty(key));
        }
    }
    
    public static Properties setProperties(ChannelCalculatorCommon calculator) throws Exception {
        String resourceName = String.format("%s.properties", calculator.getClass().getSimpleName());
        Properties properties = new Properties();
        try (InputStream in = Utility.class.getResourceAsStream(resourceName)) {
            properties.load(in);
        }
        for (String key : properties.stringPropertyNames()) {
            calculator.setProperty(key, properties.getProperty(key));
        }
        return properties;
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
