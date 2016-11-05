import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class TransferEntropyCalculator {
    private int sourceEmbedding;
    private int targetEmbedding;
    private int conditionalEmbedding;
    private ConditionalMutualInfoCalculatorMultiVariate calculator;
    
    public TransferEntropyCalculator(int sourceEmbedding, int targetEmbedding, int conditionalEmbedding) {
        this.sourceEmbedding = sourceEmbedding;
        this.targetEmbedding = targetEmbedding;
        this.conditionalEmbedding = conditionalEmbedding;
        calculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
    }
    
    public TransferEntropyCalculator(int sourceEmbedding, int targetEmbedding) {
        this(sourceEmbedding, targetEmbedding, 0);
    }
    
    public void setProperty(String key, String value) throws Exception {
        calculator.setProperty(key, value);
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
    
    private void addObservationsInternal(double[][] source, double[][] target, double[][] conditional) throws Exception {
        int embeddingMax = Math.max(Math.max(sourceEmbedding, targetEmbedding), conditionalEmbedding);
        calculator.addObservations(
            MatrixUtils.makeDelayEmbeddingVector(source, sourceEmbedding, embeddingMax - 1, source.length - embeddingMax),
            MatrixUtils.selectRows(target, embeddingMax, target.length - embeddingMax),
            MatrixUtils.appendColumns(
                MatrixUtils.makeDelayEmbeddingVector(conditional, conditionalEmbedding, embeddingMax - 1, conditional.length - embeddingMax),
                MatrixUtils.makeDelayEmbeddingVector(target, targetEmbedding, embeddingMax - 1, target.length - embeddingMax)));
    }
    
    public void addObservations(double[][] source, double[][] target, double[][] conditional) throws Exception {
        addObservationsInternal(source, target, conditional);
    }
    
    public void addObservations(double[][] source, double[][] target) throws Exception {
        addObservationsInternal(source, target, new double[source.length][0]);
    }
    
    public void finaliseAddObservations() throws Exception {
        calculator.finaliseAddObservations();
    }
    
    public double computeAverageLocalOfObservations() throws Exception {
        return calculator.computeAverageLocalOfObservations();
    }
    
    public double calculate(TimeSeriesEnsemble ensemble, int[] sourceIndices, int[] targetIndices) throws Exception {
        if (sourceIndices.length == 0 || targetIndices.length == 0) {
            return 0.0;
        }
        initialise(sourceIndices.length, targetIndices.length);
        startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            addObservations(timeSeries.get(sourceIndices), timeSeries.get(targetIndices));
        }
        finaliseAddObservations();
        return computeAverageLocalOfObservations();
    }
    
    public double calculate(TimeSeriesEnsemble ensemble, int[] sourceIndices, int[] targetIndices, int[] conditionalIndices) throws Exception {
        if (sourceIndices.length == 0 || targetIndices.length == 0) {
            return 0.0;
        }
        initialise(sourceIndices.length, targetIndices.length, conditionalIndices.length);
        startAddObservations();
        for (TimeSeries timeSeries : ensemble.getTimeSeries()) {
            addObservations(timeSeries.get(sourceIndices), timeSeries.get(targetIndices), timeSeries.get(conditionalIndices));
        }
        finaliseAddObservations();
        return computeAverageLocalOfObservations();
    }
}
