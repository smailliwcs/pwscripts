public class Nerve {
    private String name;
    private int[] neuronIndices;
    
    public Nerve(String name, int[] neuronIndices) {
        this.name = name;
        this.neuronIndices = neuronIndices;
    }
    
    public String getName() {
        return name;
    }
    
    public int[] getNeuronIndices() {
        return neuronIndices;
    }
}
