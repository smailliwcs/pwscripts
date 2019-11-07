public class Synapse {
    private int preNeuronIndex;
    private int postNeuronIndex;

    public Synapse(int preNeuronIndex, int postNeuronIndex) {
        assert preNeuronIndex != postNeuronIndex;
        this.preNeuronIndex = preNeuronIndex;
        this.postNeuronIndex = postNeuronIndex;
    }

    public int getPreNeuronIndex() {
        return preNeuronIndex;
    }

    public int getPostNeuronIndex() {
        return postNeuronIndex;
    }
}
