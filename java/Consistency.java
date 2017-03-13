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
    
    private static final Pattern INIT_AGENT_COUNT = Pattern.compile("InitAgents\\s+(?<initAgentCount>\\d+)");
    
    private static String run;
    private static boolean passive;
    private static int groupSize;
    private static EntropyCalculatorDiscrete calculator;
    private static int geneCount;
    
    public static void main(String[] args) throws Exception {
        if (!tryParseArgs(args)) {
            System.err.printf("Usage: %s RUN PASSIVE GROUP_SIZE%n", Consistency.class.getSimpleName());
            return;
        }
        System.out.printf("# groupSize = %d%n", groupSize);
        calculator = new EntropyCalculatorDiscrete(256 >> groupSize);
        Map<Integer, Collection<Event>> events = readEvents();
        Map<Integer, List<Integer>> genomes = new HashMap<Integer, List<Integer>>();
        int initAgentCount = getInitAgentCount();
        for (int agentIndex = 1; agentIndex <= initAgentCount; agentIndex++) {
            List<Integer> genome = readGenome(agentIndex);
            if (agentIndex == 1) {
                geneCount = genome.size();
            }
            genomes.put(agentIndex, genome);
        }
        System.out.printf("0 %g%n", calculate(genomes.values()));
        int timestepMax = getTimestepMax();
        for (int timestep = 1; timestep <= timestepMax; timestep++) {
            Collection<Event> timestepEvents = events.get(timestep);
            if (timestepEvents != null) {
                for (Event timestepEvent : timestepEvents) {
                    int agentIndex = timestepEvent.getAgentIndex();
                    switch (timestepEvent.getType()) {
                        case "BIRTH":
                            genomes.put(agentIndex, readGenome(agentIndex));
                            break;
                        case "DEATH":
                            genomes.remove(agentIndex);
                            break;
                        default:
                            assert false;
                    }
                }
            }
            System.out.printf("%d %g%n", timestep, calculate(genomes.values()));
        }
    }
    
    private static boolean tryParseArgs(String[] args) {
        try {
            assert args.length == 3;
            run = args[0];
            assert hasValidRun();
            passive = Boolean.parseBoolean(args[1]);
            groupSize = Integer.parseInt(args[2]);
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
                Collection<Event> timestepEvents = events.get(timestep);
                if (timestepEvents == null) {
                    timestepEvents = new LinkedList<Event>();
                    events.put(timestep, timestepEvents);
                }
                timestepEvents.add(new Event(type, agentIndex));
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
                Matcher matcher = INIT_AGENT_COUNT.matcher(line);
                if (matcher.matches()) {
                    return Integer.parseInt(matcher.group("initAgentCount"));
                }
            }
        }
    }
    
    private static int getTimestepMax() throws Exception {
        File file = new File(run, "endStep.txt");
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            return Integer.parseInt(reader.readLine());
        }
    }
    
    private static List<Integer> readGenome(int agentIndex) throws Exception {
        String pathBase = passive ? Paths.get(run, "passive").toString() : run;
        Path path = Paths.get(pathBase, "genome", "agents", String.format("genome_%d.txt.gz", agentIndex));
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
    
    private static double calculate(Collection<List<Integer>> genomes) {
        int[] genes = new int[genomes.size()];
        double sum = 0.0;
        for (int geneIndex = 0; geneIndex < geneCount; geneIndex++) {
            int genomeIndex = 0;
            for (List<Integer> genome : genomes) {
                genes[genomeIndex] = genome.get(geneIndex) >> groupSize;
                genomeIndex++;
            }
            sum += calculate(genes);
        }
        return sum / geneCount;
    }
    
    private static double calculate(int[] genes) {
        calculator.initialise();
        calculator.addObservations(genes);
        return 1.0 - calculator.computeAverageLocalOfObservations() / (8 - groupSize);
    }
}
