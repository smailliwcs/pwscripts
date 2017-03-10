import infodynamics.measures.discrete.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

public class Consistency {
    private static int base;
    private static EntropyCalculatorDiscrete calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s BASE%n", Consistency.class.getSimpleName());
            return;
        }
        System.out.printf("# base = %d%n", base);
        List<List<Integer>> genomes = new LinkedList<List<Integer>>();
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
        calculator = new EntropyCalculatorDiscrete(256 >> base);
        int[] genes = new int[genomes.size()];
        int geneCount = genomes.get(0).size();
        for (int geneIndex = 0; geneIndex < geneCount; geneIndex++) {
            for (int genomeIndex = 0; genomeIndex < genomes.size(); genomeIndex++) {
                genes[genomeIndex] = genomes.get(genomeIndex).get(geneIndex);
            }
            System.out.println(calculate(genes));
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 1;
            base = Integer.parseInt(args[0]);
            assert base >= 0 && base <= 7;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static List<Integer> readGenome(String path) throws Exception {
        List<Integer> genome = new ArrayList<Integer>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(new FileInputStream(path))))) {
            while (true) {
                String line = reader.readLine();
                if (line == null) {
                    break;
                }
                genome.add(Integer.valueOf(line));
            }
        }
        return genome;
    }
    
    private static double calculate(int[] genes) {
        calculator.initialise();
        calculator.addObservations(genes);
        return 1.0 - calculator.computeAverageLocalOfObservations() / (8 - base);
    }
}
