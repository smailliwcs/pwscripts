import java.util.*;
import java.util.stream.*;

public class Nerve {
    private String name;
    private int neuronStartIndex;
    private int neuronCount;

    public Nerve(String name, int neuronStartIndex, int neuronCount) {
        this.name = name;
        this.neuronStartIndex = neuronStartIndex;
        this.neuronCount = neuronCount;
    }

    public String getName() {
        return name;
    }

    public int getNeuronStartIndex() {
        return neuronStartIndex;
    }

    public int getNeuronCount() {
        return neuronCount;
    }

    public int getNeuronEndIndex() {
        return neuronStartIndex + neuronCount - 1;
    }

    public Collection<Integer> getNeuronIndices() {
        return IntStream.rangeClosed(neuronStartIndex, getNeuronEndIndex())
                .boxed()
                .collect(Collectors.toList());
    }

    public boolean overlaps(Nerve nerve) {
        return neuronStartIndex <= nerve.getNeuronEndIndex() && getNeuronEndIndex() >= nerve.neuronStartIndex;
    }
}
