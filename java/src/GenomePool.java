import java.util.*;

@SuppressWarnings("serial")
public class GenomePool extends LinkedList<Genome> {
    private int time;

    public int getTime() {
        return time;
    }

    public void setTime(int time) {
        this.time = time;
    }

    public int[] getGenes(int geneIndex, int groupingParameter) {
        return stream()
                .mapToInt(genome -> genome.get(geneIndex) >> groupingParameter)
                .toArray();
    }
}
