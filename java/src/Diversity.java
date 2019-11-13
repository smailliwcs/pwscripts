import java.io.*;
import java.util.*;
import java.util.stream.*;

import infodynamics.measures.discrete.*;

public class Diversity {
    private static class Calculator extends EntropyCalculatorDiscrete {
        private int grouping;
        private int geneCount;

        public Calculator(int grouping, int geneCount) {
            super(1 << (8 - grouping));
            this.grouping = grouping;
            this.geneCount = geneCount;
        }

        private double getDiversity(Collection<Iterator<Integer>> genes) {
            initialise();
            addObservations(
                    genes.stream()
                            .mapToInt(gene -> gene.next())
                            .toArray());
            return computeAverageLocalOfObservations() / (8 - grouping);
        }

        public double getDiversity(GenomePool pool) {
            Collection<Iterator<Integer>> genes = pool.values()
                    .stream()
                    .map(genome -> genome.iterator())
                    .collect(Collectors.toList());
            return IntStream.range(0, geneCount)
                    .mapToDouble(geneIndex -> getDiversity(genes))
                    .average()
                    .getAsDouble();
        }
    }

    private static class Arguments {
        public static Arguments parse(Queue<String> args) {
            try {
                int grouping = Integer.parseInt(args.remove());
                assert grouping >= 0 && grouping < 8;
                assert args.isEmpty();
                return new Arguments(grouping);
            } catch (Throwable e) {
                printUsage(System.err);
                System.exit(1);
                return null;
            }
        }

        public static void printUsage(PrintStream out) {
            out.printf("Usage: %s GROUPING%n", Diversity.class.getSimpleName());
        }

        public final int grouping;

        private Arguments(int grouping) {
            this.grouping = grouping;
        }

        public void print(PrintStream out) {
            out.printf("# grouping = %d%n", grouping);
        }
    }

    public static void main(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(new LinkedList<String>(Arrays.asList(args)));
        arguments.print(System.out);
        try (GenomePoolReader reader = new GenomePoolReader(new InputStreamReader(System.in))) {
            Calculator calculator = new Calculator(arguments.grouping, reader.readSize());
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
