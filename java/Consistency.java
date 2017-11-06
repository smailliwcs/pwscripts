import infodynamics.measures.discrete.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.util.zip.*;

public class Consistency {
    private static class Event {
        private String type;
        private int agentIndex;
        
        public Event(String type, int agentIndex) {
            this.type = type;
            this.agentIndex = agentIndex;
        }
        
        public String getType() {
            return type;
        }
        
        public int getAgentIndex() {
            return agentIndex;
        }
    }
    
    private static final Pattern INIT_AGENTS = Pattern.compile("InitAgents\\s+(?<initAgentCount>\\d+)");
    
    private static String run;
    private static int groupSize;
    private static EntropyCalculatorDiscrete calculator;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s RUN GROUP_SIZE%n", Consistency.class.getSimpleName());
            return;
        }
        System.out.printf("# group_size = %d%n", groupSize);
        calculator = new EntropyCalculatorDiscrete(256 >> groupSize);
        Map<Integer, Collection<Event>> events = readEvents();
        Map<Integer, List<Integer>> genomes = new HashMap<Integer, List<Integer>>();
        int initAgentCount = getInitAgentCount();
        for (int agentIndex = 1; agentIndex <= initAgentCount; agentIndex++) {
            genomes.put(agentIndex, readGenome(agentIndex));
        }
        System.out.printf("0 %g%n", getConsistency(genomes.values()));
        int maxTimestep = getMaxTimestep();
        for (int timestep = 1; timestep <= maxTimestep; timestep++) {
            for (Event event : events.get(timestep)) {
                int agentIndex = event.getAgentIndex();
                switch (event.getType()) {
                    case "BIRTH":
                        genomes.put(agentIndex, readGenome(agentIndex));
                        break;
                    case "DEATH":
                        genomes.remove(agentIndex);
                        break;
                    case "VIRTUAL":
                        break;
                    default:
                        assert false;
                }
            }
            System.out.printf("%d %g%n", timestep, getConsistency(genomes.values()));
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 2;
            int index = 0;
            run = args[index++];
            assert hasValidRun();
            groupSize = Integer.parseInt(args[index++]);
            assert groupSize >= 0 && groupSize <= 7;
            return true;
        } catch (Throwable ex) {
            return false;
        }
    }
    
    private static boolean hasValidRun() {
        File file = new File(run, "endStep.txt");
        return file.exists();
    }
    
    private static Map<Integer, Collection<Event>> readEvents() throws Exception {
        Map<Integer, Collection<Event>> events = new HashMap<Integer, Collection<Event>>();
        int maxTimestep = getMaxTimestep();
        for (int timestep = 1; timestep <= maxTimestep; timestep++) {
            events.put(timestep, new LinkedList<Event>());
        }
        File file = new File(run, "BirthsDeaths.log");
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            while (true) {
                String line = reader.readLine();
                if (line == null) {
                    break;
                }
                if (line.startsWith("%")) {
                    continue;
                }
                Scanner scanner = new Scanner(line);
                int timestep = scanner.nextInt();
                String type = scanner.next();
                int agentIndex = scanner.nextInt();
                events.get(timestep).add(new Event(type, agentIndex));
            }
        }
        return events;
    }
    
    private static int getInitAgentCount() throws Exception {
        File file = new File(run, "normalized.wf");
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            while (true) {
                String line = reader.readLine();
                assert line != null;
                Matcher matcher = INIT_AGENTS.matcher(line);
                if (matcher.matches()) {
                    return Integer.parseInt(matcher.group("initAgentCount"));
                }
            }
        }
    }
    
    private static int getMaxTimestep() throws Exception {
        File file = new File(run, "endStep.txt");
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            return Integer.parseInt(reader.readLine());
        }
    }
    
    private static List<Integer> readGenome(int agentIndex) throws Exception {
        Path path = Paths.get(run, "genome", "agents", String.format("genome_%d.txt.gz", agentIndex));
        File file = new File(path.toString());
        List<Integer> genome = new ArrayList<Integer>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(new FileInputStream(file))))) {
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
    
    private static double getConsistency(Collection<List<Integer>> genomes) {
        double entropy = 0.0;
        int[] genes = new int[genomes.size()];
        int geneCount = genomes.iterator().next().size();
        for (int geneIndex = 0; geneIndex < geneCount; geneIndex++) {
            int genomeIndex = 0;
            for (List<Integer> genome : genomes) {
                genes[genomeIndex] = genome.get(geneIndex) >> groupSize;
                genomeIndex++;
            }
            entropy += getEntropy(genes);
        }
        return 1.0 - entropy / geneCount;
    }
    
    private static double getEntropy(int[] genes) {
        calculator.initialise();
        calculator.addObservations(genes);
        return calculator.computeAverageLocalOfObservations() / (8 - groupSize);
    }
}
