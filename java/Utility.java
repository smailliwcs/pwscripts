import infodynamics.measures.continuous.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;

public class Utility {
    public static int[] getRange(int start, int count) {
        int[] range = new int[count];
        for (int index = 0; index < count; index++) {
            range[index] = start + index;
        }
        return range;
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
    
    public static Properties setProperties(Object calculator) throws Exception {
        String resourceName = String.format("%s.properties", calculator.getClass().getSimpleName());
        Properties properties = new Properties();
        try (InputStream in = Utility.class.getResourceAsStream(resourceName)) {
            if (in == null) {
                return null;
            }
            properties.load(in);
        }
        Method method = calculator.getClass().getMethod("setProperty", String.class, String.class);
        for (String key : properties.stringPropertyNames()) {
            method.invoke(calculator, key, properties.getProperty(key));
        }
        return properties;
    }
    
    public static Properties setProperties(Object calculator, PrintStream out) throws Exception {
        Properties properties = setProperties(calculator);
        printProperties(properties, out);
        return properties;
    }
    
    public static void printProperties(Properties properties, PrintStream out) {
        if (properties == null) {
            return;
        }
        for (String key : properties.stringPropertyNames()) {
            out.printf("# %s = %s%n", key, properties.getProperty(key));
        }
    }
}
