import java.io.*;
import java.util.regex.*;

public class GenomePoolReader extends BufferedReader {
    private static final Pattern SIZE_PATTERN = Pattern.compile("^# SIZE (?<size>\\d+)$");
    private static final Pattern STEP_PATTERN = Pattern.compile("^# STEP (?<step>\\d+)$");
    private static final Pattern SPACE_PATTERN = Pattern.compile(" ");

    private int size;

    public GenomePoolReader(Reader in) {
        super(in);
    }

    public int getSize() {
        return size;
    }

    public void readSize() throws IOException {
        String line = readLine();
        Matcher matcher = SIZE_PATTERN.matcher(line);
        boolean isMatch = matcher.matches();
        assert isMatch;
        size = Integer.parseInt(matcher.group("size"));
    }

    public GenomePool readGenomePool() throws IOException {
        String line = readLine();
        if (line == null) {
            return null;
        }
        GenomePool pool = new GenomePool();
        while (true) {
            Matcher matcher = STEP_PATTERN.matcher(line);
            if (matcher.matches()) {
                int time = Integer.parseInt(matcher.group("step"));
                pool.setTime(time);
                break;
            }
            assert line.equals("# BEGIN GENOME");
            pool.add(readGenome());
            line = readLine();
            assert line.equals("# END GENOME");
            line = readLine();
        }
        return pool;
    }

    private Genome readGenome() throws IOException {
        Genome genome = new Genome();
        while (genome.size() < size) {
            String line = readLine();
            SPACE_PATTERN.splitAsStream(line)
                    .map(Integer::valueOf)
                    .forEach(genome::add);
        }
        return genome;
    }
}
