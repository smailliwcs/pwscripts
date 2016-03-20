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
    
    public Iterable<Synapse> getSynapses() {
        return synapses;
    }
    
    public void addSynapse(Synapse synapse) {
        synapses.add(synapse);
    }
    
    public Iterable<TimeSeries> getTimeSeries() {
        return timeSeries;
    }
    
    public void addTimeSeries(TimeSeries timeSeries) {
        this.timeSeries.add(timeSeries);
    }
}
