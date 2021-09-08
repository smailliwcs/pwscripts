import java.io.*;
import java.util.regex.*;

public class GenomePoolReader extends InputStreamReader {
    private static final Pattern GENES_PATTERN = Pattern.compile("^# GENES (?<geneCount>\\d+)$");
    private static final Pattern AGENTS_PATTERN = Pattern.compile("^# AGENTS (?<agentCount>\\d+)$");
    private static final Pattern STEP_PATTERN = Pattern.compile("^# STEP (?<time>\\d+)$");

    private InputStream in;
    private int geneCount;
    private byte[] buffer;

    public GenomePoolReader(InputStream in) {
        super(in);
        this.in = in;
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
        buffer = new byte[geneCount];
    }

    public GenomePool readGenomePool() throws IOException {
        int agentCount = readAgentCount();
        if (agentCount == -1) {
            return null;
        }
        GenomePool pool = new GenomePool();
        for (int agentIndex = 0; agentIndex < agentCount; agentIndex++) {
            pool.add(readGenome());
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

    private Genome readGenome() throws IOException {
        Genome genome = new Genome(geneCount);
        while (true) {
            int count = in.read(buffer, 0, geneCount - genome.size());
            if (count == -1) {
                throw new EOFException();
            }
            for (int index = 0; index < count; index++) {
                genome.add(buffer[index] & 0xff);
            }
            if (genome.size() == geneCount) {
                break;
            }
        }
        return genome;
    }

    private int readTime() throws IOException {
        String line = readLine();
        Matcher matcher = STEP_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        return Integer.parseInt(matcher.group("time"));
    }
}
