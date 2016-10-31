import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class TransferEntropyCalculator {
    private int embeddingLength;
    private ConditionalMutualInfoCalculatorMultiVariate calculator;
    
    public TransferEntropyCalculator(int embeddingLength) {
        this.embeddingLength = embeddingLength;
        calculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
    }
    
    public void setProperty(String key, String value) throws Exception {
        calculator.setProperty(key, value);
    }
    
    public void initialise(int sourceDimension, int targetDimension, int conditionalDimension) throws Exception {
        calculator.initialise(embeddingLength * sourceDimension, targetDimension, embeddingLength * (targetDimension + conditionalDimension));
    }
    
    public void initialise(int sourceDimension, int targetDimension) throws Exception {
        initialise(sourceDimension, targetDimension, 0);
    }
    
    public void startAddObservations() {
        calculator.startAddObservations();
    }
    
    private void addObservationsInternal(double[][] source, double[][] target, double[][] conditional) throws Exception {
        calculator.addObservations(
            MatrixUtils.makeDelayEmbeddingVector(source, embeddingLength, embeddingLength - 1, source.length - embeddingLength),
            MatrixUtils.selectRows(target, embeddingLength, target.length - embeddingLength),
            MatrixUtils.makeDelayEmbeddingVector(conditional, embeddingLength, embeddingLength - 1, conditional.length - embeddingLength));
    }
    
    public void addObservations(double[][] source, double[][] target, double[][] conditional) throws Exception {
        addObservationsInternal(source, target, MatrixUtils.appendColumns(conditional, target));
    }
    
    public void addObservations(double[][] source, double[][] target) throws Exception {
        addObservationsInternal(source, target, target);
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
