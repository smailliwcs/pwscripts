import java.io.*;
import java.util.*;
import java.util.stream.*;

import infodynamics.measures.discrete.*;

public class Diversity {
    private static class Calculator extends EntropyCalculatorDiscrete {
        private int groupingParameter;
        private int geneCount;

        public Calculator(int groupingParameter, int geneCount) {
            super(1 << (8 - groupingParameter));
            this.groupingParameter = groupingParameter;
            this.geneCount = geneCount;
        }

        private double getDiversity(Collection<Iterator<Integer>> genes) {
            initialise();
            addObservations(genes.stream()
                    .mapToInt(gene -> gene.next() >> groupingParameter)
                    .toArray());
            return computeAverageLocalOfObservations() / (8 - groupingParameter);
        }

        public double getDiversity(GenomePool pool) {
            Collection<Iterator<Integer>> genes = pool.values()
                    .stream()
                    .map(Genome::iterator)
                    .collect(Collectors.toList());
            return DoubleStream.generate(() -> getDiversity(genes))
                    .limit(geneCount)
                    .average()
                    .getAsDouble();
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
        System.out.println("time value");
        try (GenomePoolReader reader = new GenomePoolReader(new InputStreamReader(System.in))) {
            Calculator calculator = new Calculator(arguments.groupingParameter, reader.readSize());
            double diversity = 0.0;
            while (true) {
                GenomePool pool = reader.readGenomePool();
                if (pool == null) {
                    break;
                }
                if (pool.isDirty()) {
                    diversity = calculator.getDiversity(pool);
                }
                System.out.printf("%d %g%n", pool.getTime(), diversity);
            }
        }
    }
}
