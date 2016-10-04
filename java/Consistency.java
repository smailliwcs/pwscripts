import infodynamics.measures.discrete.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

public class Consistency {
    private static int base;
    private static EntropyCalculatorDiscrete calculator;
    
    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException();
        }
        base = Integer.parseInt(args[0]);
        if (base < 0 || base > 7) {
            throw new IllegalArgumentException();
        }
        Collection<Iterator<Integer>> genomes = new LinkedList<Iterator<Integer>>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
            while (true) {
                String path = reader.readLine();
                if (path == null) {
                    break;
                }
                genomes.add(readGenome(path));
            }
        }
        if (genomes.size() == 0) {
            return;
        }
        Collection<Integer> values = new LinkedList<Integer>();
        calculator = new EntropyCalculatorDiscrete(256 >> base);
        while (genomes.iterator().next().hasNext()) {
            values.clear();
            for (Iterator<Integer> genome : genomes) {
                values.add(genome.next() >> base);
            }
            System.out.println(calculate(Utility.toPrimitive(values)));
        }
    }
    
    private static Iterator<Integer> readGenome(String path) throws Exception {
        Collection<Integer> genome = new LinkedList<Integer>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(new FileInputStream(path))))) {
            while (true) {
                String line = reader.readLine();
                if (line == null) {
                    break;
                }
                genome.add(Integer.parseInt(line));
            }
        }
        return genome.iterator();
    }
    
    private static double calculate(int[] values) {
        calculator.initialise();
        calculator.addObservations(values);
        return 1.0 - calculator.computeAverageLocalOfObservations() / (8 - base);
    }
}
