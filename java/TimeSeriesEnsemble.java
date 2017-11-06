import java.util.*;

public class TimeSeriesEnsemble extends LinkedList<TimeSeries> {
    private static int[] getRange(int start, int count) {
        int[] range = new int[count];
        for (int index = 0; index < count; index++) {
            range[index] = start + index;
        }
        return range;
    }
    
    private int agentIndex;
    private int neuronCount;
    private int inputNeuronCount;
    private int outputNeuronCount;
    private Collection<Synapse> synapses;
    
    public TimeSeriesEnsemble(int agentIndex, int neuronCount, int inputNeuronCount, int outputNeuronCount) {
        this.agentIndex = agentIndex;
        this.neuronCount = neuronCount;
        this.inputNeuronCount = inputNeuronCount;
        this.outputNeuronCount = outputNeuronCount;
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
        return getRange(0, neuronCount);
    }
    
    public int[] getInputNeuronIndices() {
        return getRange(0, inputNeuronCount);
    }
    
    public int[] getOutputNeuronIndices() {
        return getRange(inputNeuronCount, outputNeuronCount);
    }
    
    public int[] getInternalNeuronIndices() {
        return getRange(inputNeuronCount + outputNeuronCount, getInternalNeuronCount());
    }
    
    public int[] getProcessingNeuronIndices() {
        return getRange(inputNeuronCount, getProcessingNeuronCount());
    }
    
    public Iterable<Synapse> getSynapses() {
        return synapses;
    }
    
    public void addSynapse(Synapse synapse) {
        synapses.add(synapse);
    }
    
    public TimeSeries combine() {
        switch (size()) {
            case 0:
                return null;
            case 1:
                return getFirst();
            default:
                int capacity = size() * getFirst().size();
                TimeSeries combinedTimeSeries = new TimeSeries(neuronCount, capacity);
                for (TimeSeries timeSeries : this) {
                    for (double[] row : timeSeries) {
                        combinedTimeSeries.add(row);
                    }
                }
                return combinedTimeSeries;
        }
    }
}
