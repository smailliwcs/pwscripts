import java.io.*;
import java.util.*;
import java.util.regex.*;

public class GenomePoolReader extends InputStreamReader {
    private static final Pattern GENES_PATTERN = Pattern.compile("^# GENES (?<geneCount>\\d+)$");
    private static final Pattern AGENTS_PATTERN = Pattern.compile("^# AGENTS (?<agentCount>\\d+)$");
    private static final Pattern STEP_PATTERN = Pattern.compile("^# STEP (?<time>\\d+)$");

    private InputStream in;
    private List<Genome> genomes;
    private int geneCount;

    public GenomePoolReader(InputStream in) {
        super(in);
        this.in = in;
        genomes = new ArrayList<Genome>();
    }

    private String readLine() throws IOException {
        int ch = in.read();
        if (ch == -1) {
            return null;
        }
        if (ch == '\n') {
            return "";
        }
        StringBuilder line = new StringBuilder();
        while (true) {
            line.append((char)ch);
            ch = in.read();
            if (ch == -1 || ch == '\n') {
                break;
            }
        }
        return line.toString();
    }

    public int getGeneCount() {
        return geneCount;
    }

    public void readGeneCount() throws IOException {
        String line = readLine();
        Matcher matcher = GENES_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        geneCount = Integer.parseInt(matcher.group("geneCount"));
    }

    public GenomePool readGenomePool() throws IOException {
        int agentCount = readAgentCount();
        if (agentCount == -1) {
            return null;
        }
        GenomePool pool = new GenomePool();
        for (int agentIndex = 0; agentIndex < agentCount; agentIndex++) {
            Genome genome;
            if (agentIndex == genomes.size()) {
                genome = new Genome(geneCount);
                genomes.add(genome);
            } else {
                genome = genomes.get(agentIndex);
            }
            genome.read(in);
            pool.add(genome);
        }
        pool.setTime(readTime());
        return pool;
    }

    private int readAgentCount() throws IOException {
        String line = readLine();
        if (line == null) {
            return -1;
        }
        Matcher matcher = AGENTS_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        return Integer.parseInt(matcher.group("agentCount"));
    }

    private int readTime() throws IOException {
        String line = readLine();
        Matcher matcher = STEP_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        return Integer.parseInt(matcher.group("time"));
    }
}
