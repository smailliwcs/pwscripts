import java.util.*;

public class TimeSeriesEnsemble extends LinkedList<TimeSeries> {
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
    
    public int[] getPreNeuronIndices(int postNeuronIndex) {
        Collection<Integer> preNeuronIndices = new LinkedList<Integer>();
        for (Synapse synapse : synapses) {
            if (synapse.getPostNeuronIndex() == postNeuronIndex) {
                assert synapse.getPreNeuronIndex() != postNeuronIndex;
                preNeuronIndices.add(synapse.getPreNeuronIndex());
            }
        }
        return Utility.toPrimitive(preNeuronIndices);
    }
    
    public Iterable<Nerve> getNerves() {
        return nerves;
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
