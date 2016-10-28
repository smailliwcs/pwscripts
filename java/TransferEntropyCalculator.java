import infodynamics.measures.continuous.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

public class TransferEntropyCalculator {
    private int k;
    private ConditionalMutualInfoCalculatorMultiVariate calculator;
    
    public TransferEntropyCalculator(int k) {
        this.k = k;
        calculator = new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
    }
    
    public void setProperty(String key, String value) throws Exception {
        calculator.setProperty(key, value);
    }
    
    public void initialise(int d_source, int d_target, int d_conditional) throws Exception {
        calculator.initialise(k * d_source, d_target, k * (d_target + d_conditional));
    }
    
    public void initialise(int d_source, int d_target) throws Exception {
        initialise(d_source, d_target, 0);
    }
    
    public void startAddObservations() {
        calculator.startAddObservations();
    }
    
    private void addObservationsInternal(double[][] source, double[][] target, double[][] conditional) throws Exception {
        calculator.addObservations(
            MatrixUtils.makeDelayEmbeddingVector(source, k, k - 1, source.length - k),
            MatrixUtils.selectRows(target, k, target.length - k),
            MatrixUtils.makeDelayEmbeddingVector(conditional, k, k - 1, conditional.length - k));
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
