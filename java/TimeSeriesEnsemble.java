import java.util.*;

public class TimeSeriesEnsemble {
    private int agentIndex;
    private int neuronCount;
    private int inputNeuronCount;
    private int outputNeuronCount;
    private Collection<Synapse> synapses;
    private Collection<TimeSeries> timeSeries;
    
    public TimeSeriesEnsemble(int agentIndex, int neuronCount, int inputNeuronCount, int outputNeuronCount) {
        this.agentIndex = agentIndex;
        this.neuronCount = neuronCount;
        this.inputNeuronCount = inputNeuronCount;
        this.outputNeuronCount = outputNeuronCount;
        synapses = new LinkedList<Synapse>();
        timeSeries = new LinkedList<TimeSeries>();
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
    
    public Collection<Synapse> getSynapses() {
        return synapses;
    }
    
    public void addSynapse(Synapse synapse) {
        synapses.add(synapse);
    }
    
    public Collection<TimeSeries> getTimeSeries() {
        return timeSeries;
    }
    
    public void addTimeSeries(TimeSeries timeSeries) {
        this.timeSeries.add(timeSeries);
    }
}
