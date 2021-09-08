import java.io.*;
import java.util.*;
import java.util.stream.*;

import infodynamics.measures.discrete.*;

public class Diversity {
    private static class Calculator extends EntropyCalculatorDiscrete {
        private int groupingParameter;

        public Calculator(int groupingParameter) {
            super(1 << (8 - groupingParameter));
            this.groupingParameter = groupingParameter;
        }

        public double getDiversity(GenomePool pool, int geneIndex) {
            initialise();
            addObservations(pool.getGenes(geneIndex, groupingParameter));
            return computeAverageLocalOfObservations() / (8 - groupingParameter);
        }
    }

    private static class Arguments {
        private static String getUsage() {
            StringBuilder usage = new StringBuilder();
            usage.append("Usage: %s GROUPING%n");
            usage.append("%n");
            usage.append("  GROUPING  Allele grouping parameter%n");
            return usage.toString();
        }

        public static Arguments parse(String[] args) {
            try (ArgumentParser parser = new ArgumentParser(getUsage(), Diversity.class.getName(), args)) {
                int groupingParameter = parser.parse(
                        Integer::parseInt,
                        argument -> argument >= 0 && argument <= 7,
                        "Invalid allele grouping parameter (choose from [0, 7])");
                return new Arguments(groupingParameter);
            }
        }

        public final int groupingParameter;

        private Arguments(int groupingParameter) {
            this.groupingParameter = groupingParameter;
        }

        public String toString() {
            StringBuilder result = new StringBuilder();
            result.append(String.format("# GROUPING = %d%n", groupingParameter));
            return result.toString();
        }
    }

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(args);
        System.out.print(arguments);
        try (GenomePoolReader reader = new GenomePoolReader(System.in)) {
            reader.readGeneCount();
            System.out.print("time");
            for (int geneIndex = 0; geneIndex < reader.getGeneCount(); geneIndex++) {
                System.out.printf(" value%d", geneIndex);
            }
            System.out.println();
            Calculator calculator = new Calculator(arguments.groupingParameter);
            while (true) {
                GenomePool pool = reader.readGenomePool();
                if (pool == null) {
                    break;
                }
                System.out.print(pool.getTime());
                for (int geneIndex = 0; geneIndex < reader.getGeneCount(); geneIndex++) {
                    double diversity = calculator.getDiversity(pool, geneIndex);
                    System.out.printf(" %.3g", diversity);
                }
                System.out.println();
            }
        }
    }
}
