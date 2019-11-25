import java.io.*;
import java.util.regex.*;

public class GenomePoolReader extends BufferedReader {
    private static final Pattern SIZE_PATTERN = Pattern.compile("^SIZE (?<size>\\d+)$");
    private static final Pattern SPACE_PATTERN = Pattern.compile(" ");

    private GenomePool pool = new GenomePool();

    public GenomePoolReader(Reader in) {
        super(in);
    }

    public int readSize() throws IOException {
        String line = readLine();
        Matcher matcher = SIZE_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        return Integer.parseInt(matcher.group("size"));
    }

    public GenomePool readGenomePool() throws IOException {
        String line = readLine();
        if (line == null) {
            return null;
        }
        pool.setDirty(false);
        while (true) {
            String[] chunks = SPACE_PATTERN.split(line);
            String event = chunks[0];
            if (event.equals("STEP")) {
                pool.setTime(Integer.parseInt(chunks[1]));
                break;
            }
            if (event.equals("BIRTH") || event.equals("DEATH")) {
                int agentId = Integer.parseInt(chunks[1]);
                switch (event) {
                case "BIRTH":
                    assert !pool.containsKey(agentId);
                    pool.put(agentId, readGenome());
                    break;
                case "DEATH":
                    assert pool.containsKey(agentId);
                    pool.remove(agentId);
                    break;
                }
                pool.setDirty(true);
            } else {
                assert false;
            }
            line = readLine();
        }
        return pool;
    }

    private Genome readGenome() throws IOException {
        Genome genome = new Genome();
        while (true) {
            String line = readLine();
            if (line.isEmpty()) {
                break;
            }
            genome.add(Integer.parseInt(line));
        }
        return genome;
    }
}
