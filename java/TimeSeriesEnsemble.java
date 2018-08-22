import java.util.*;

public class TimeSeriesEnsemble extends ArrayList<TimeSeries> {
    private int agentIndex;
    private int neuronCount;
    private int inputNeuronCount;
    private int outputNeuronCount;
    private Collection<Nerve> nerves;
    private Collection<Synapse> synapses;
    
    public TimeSeriesEnsemble(int agentIndex, int neuronCount, int inputNeuronCount, int outputNeuronCount) {
        this.agentIndex = agentIndex;
        this.neuronCount = neuronCount;
        this.inputNeuronCount = inputNeuronCount;
        this.outputNeuronCount = outputNeuronCount;
        nerves = new LinkedList<Nerve>();
        synapses = new LinkedList<Synapse>();
    }
    
    public int getAgentIndex() {
        return agentIndex;
    }
    
    public int getNeuronCount() {
        return neuronCount;
    }
    
    public int getInputNeuronCount() {
        return inputNeuronCount;
    }
    
    public int getOutputNeuronCount() {
        return outputNeuronCount;
    }
    
    public int getInternalNeuronCount() {
        return neuronCount - inputNeuronCount - outputNeuronCount;
    }
    
    public int getProcessingNeuronCount() {
        return neuronCount - inputNeuronCount;
    }
    
    public int[] getNeuronIndices() {
        return Utility.getRange(0, neuronCount);
    }
    
    public int[] getInputNeuronIndices() {
        return Utility.getRange(0, inputNeuronCount);
    }
    
    public int[] getOutputNeuronIndices() {
        return Utility.getRange(inputNeuronCount, outputNeuronCount);
    }
    
    public int[] getInternalNeuronIndices() {
        return Utility.getRange(inputNeuronCount + outputNeuronCount, getInternalNeuronCount());
    }
    
    public int[] getProcessingNeuronIndices() {
        return Utility.getRange(inputNeuronCount, getProcessingNeuronCount());
    }
    
    public int getProcessingNeuronOffset(int neuronIndex) {
        assert neuronIndex >= inputNeuronCount;
        return neuronIndex - inputNeuronCount;
    }
    
    public int[] getPreNeuronIndices(int postNeuronIndex, int preNeuronIndexToSkip) {
        Collection<Integer> preNeuronIndices = new LinkedList<Integer>();
        for (Synapse synapse : synapses) {
            if (synapse.getPostNeuronIndex() == postNeuronIndex) {
                int preNeuronIndex = synapse.getPreNeuronIndex();
                if (preNeuronIndex != preNeuronIndexToSkip) {
                    preNeuronIndices.add(preNeuronIndex);
                }
            }
        }
        return Utility.toPrimitive(preNeuronIndices);
    }
    
    public int[] getPostNeuronIndices(int preNeuronIndex) {
        Collection<Integer> postNeuronIndices = new LinkedList<Integer>();
        for (Synapse synapse : synapses) {
            if (synapse.getPreNeuronIndex() == preNeuronIndex) {
                postNeuronIndices.add(synapse.getPostNeuronIndex());
            }
        }
        return Utility.toPrimitive(postNeuronIndices);
    }
    
    public Iterable<Nerve> getNerves() {
        return nerves;
    }
    
    public Iterable<Nerve> getInputNerves() {
        Collection<Nerve> inputNerves = new LinkedList<Nerve>();
        for (Nerve nerve : nerves) {
            int[] neuronIndices = nerve.getNeuronIndices();
            if (neuronIndices[neuronIndices.length - 1] >= inputNeuronCount) {
                assert neuronIndices[0] == inputNeuronCount;
                break;
            }
            inputNerves.add(nerve);
        }
        return inputNerves;
    }
    
    public void addNerve(Nerve nerve) {
        nerves.add(nerve);
    }
    
    public Iterable<Synapse> getSynapses() {
        return synapses;
    }
    
    public void addSynapse(Synapse synapse) {
        synapses.add(synapse);
    }
}
