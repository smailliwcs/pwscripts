import infodynamics.measures.continuous.*;
import infodynamics.utils.*;

public class ConditionalTransferEntropyCalculatorMultiVariate {
    private ConditionalMutualInfoCalculatorMultiVariate calculator;
    private int sourceEmbedding;
    private int targetEmbedding;
    private int conditionalEmbedding;
    
    public ConditionalTransferEntropyCalculatorMultiVariate(ConditionalMutualInfoCalculatorMultiVariate calculator, int sourceEmbedding, int targetEmbedding, int conditionalEmbedding) {
        this.calculator = calculator;
        this.sourceEmbedding = sourceEmbedding;
        this.targetEmbedding = targetEmbedding;
        this.conditionalEmbedding = conditionalEmbedding;
    }
    
    public ConditionalTransferEntropyCalculatorMultiVariate(ConditionalMutualInfoCalculatorMultiVariate calculator, int sourceEmbedding, int targetEmbedding) {
        this(calculator, sourceEmbedding, targetEmbedding, 0);
    }
    
    public void initialise(int sourceDimension, int targetDimension, int conditionalDimension) throws Exception {
        calculator.initialise(
            sourceEmbedding * sourceDimension,
            targetDimension,
            targetEmbedding * targetDimension + conditionalEmbedding * conditionalDimension);
    }
    
    public void initialise(int sourceDimension, int targetDimension) throws Exception {
        initialise(sourceDimension, targetDimension, 0);
    }
    
    public void startAddObservations() {
        calculator.startAddObservations();
    }
    
    public void addObservations(double[][] source, double[][] target, double[][] conditional) throws Exception {
        int embeddingMax = Math.max(Math.max(sourceEmbedding, targetEmbedding), conditionalEmbedding);
        calculator.addObservations(
            MatrixUtils.makeDelayEmbeddingVector(source, sourceEmbedding, embeddingMax - 1, source.length - embeddingMax),
            MatrixUtils.selectRows(target, embeddingMax, target.length - embeddingMax),
            MatrixUtils.appendColumns(
                MatrixUtils.makeDelayEmbeddingVector(conditional, conditionalEmbedding, embeddingMax - 1, conditional.length - embeddingMax),
                MatrixUtils.makeDelayEmbeddingVector(target, targetEmbedding, embeddingMax - 1, target.length - embeddingMax)));
    }
    
    public void addObservations(double[][] source, double[][] target) throws Exception {
        addObservations(source, target, new double[source.length][0]);
    }
    
    public void finaliseAddObservations() throws Exception {
        calculator.finaliseAddObservations();
    }
    
    public double computeAverageLocalOfObservations() throws Exception {
        return calculator.computeAverageLocalOfObservations();
    }
}
