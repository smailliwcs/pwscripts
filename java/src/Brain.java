import java.util.*;
import java.util.stream.*;

public class Brain {
    public static enum Layer {
        ALL("All"),
        INPUT("Input"),
        PROCESSING("Processing"),
        OUTPUT("Output"),
        INTERNAL("Internal");

        private String name;

        private Layer(String name) {
            this.name = name;
        }

        public String getName() {
            return name;
        }
    }

    private int neuronCount;
    private int inputNeuronCount;
    private int outputNeuronCount;
    private Collection<Nerve> nerves = new LinkedList<Nerve>();
    private Collection<Synapse> synapses = new LinkedList<Synapse>();

    public Brain(int neuronCount, int inputNeuronCount, int outputNeuronCount) {
        this.neuronCount = neuronCount;
        this.inputNeuronCount = inputNeuronCount;
        this.outputNeuronCount = outputNeuronCount;
    }

    public boolean isValidNeuronIndex(int neuronIndex) {
        return neuronIndex >= 0 && neuronIndex < neuronCount;
    }

    public Layer getLayerForNeuronIndex(int neuronIndex) {
        assert isValidNeuronIndex(neuronIndex);
        if (neuronIndex < inputNeuronCount) {
            return Layer.INPUT;
        }
        if (neuronIndex < inputNeuronCount + outputNeuronCount) {
            return Layer.OUTPUT;
        }
        return Layer.INTERNAL;
    }

    public int getNeuronStartIndex(Layer layer) {
        switch (layer) {
        case ALL:
            return 0;
        case INPUT:
            return 0;
        case PROCESSING:
            return inputNeuronCount;
        case OUTPUT:
            return inputNeuronCount;
        case INTERNAL:
            return inputNeuronCount + outputNeuronCount;
        default:
            assert false;
            return -1;
        }
    }

    public int getNeuronCount(Layer layer) {
        switch (layer) {
        case ALL:
            return neuronCount;
        case INPUT:
            return inputNeuronCount;
        case PROCESSING:
            return neuronCount - inputNeuronCount;
        case OUTPUT:
            return outputNeuronCount;
        case INTERNAL:
            return neuronCount - inputNeuronCount - outputNeuronCount;
        default:
            assert false;
            return 0;
        }
    }

    public int getNeuronCount() {
        return getNeuronCount(Layer.ALL);
    }

    public int getNeuronEndIndex(Layer layer) {
        return getNeuronStartIndex(layer) + getNeuronCount(layer) - 1;
    }

    public Collection<Integer> getNeuronIndices(Layer layer) {
        return IntStream.rangeClosed(getNeuronStartIndex(layer), getNeuronEndIndex(layer))
                .boxed()
                .collect(Collectors.toList());
    }

    public Collection<Integer> getNeuronIndices() {
        return getNeuronIndices(Layer.ALL);
    }

    public boolean addNerve(Nerve nerve) {
        assert getLayerForNeuronIndex(nerve.getNeuronStartIndex()) == getLayerForNeuronIndex(nerve.getNeuronEndIndex());
        assert nerves.stream().noneMatch(nerve::overlaps);
        return nerves.add(nerve);
    }

    public Collection<Nerve> getNerves(Layer layer) {
        return nerves.stream()
                .filter(nerve -> getLayerForNeuronIndex(nerve.getNeuronStartIndex()) == layer)
                .collect(Collectors.toList());
    }

    public boolean addSynapse(Synapse synapse) {
        assert isValidNeuronIndex(synapse.getPreNeuronIndex());
        assert isValidNeuronIndex(synapse.getPostNeuronIndex());
        assert getLayerForNeuronIndex(synapse.getPostNeuronIndex()) != Layer.INPUT;
        return synapses.add(synapse);
    }

    public Collection<Integer> getPreNeuronIndices(int postNeuronIndex) {
        return synapses.stream()
                .filter(synapse -> synapse.getPostNeuronIndex() == postNeuronIndex)
                .map(Synapse::getPreNeuronIndex)
                .collect(Collectors.toList());
    }

    public Collection<Integer> getPostNeuronIndices(int preNeuronIndex) {
        return synapses.stream()
                .filter(synapse -> synapse.getPreNeuronIndex() == preNeuronIndex)
                .map(Synapse::getPostNeuronIndex)
                .collect(Collectors.toList());
    }
}
