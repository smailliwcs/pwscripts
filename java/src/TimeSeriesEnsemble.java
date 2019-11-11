import java.util.*;
import java.util.stream.*;

@SuppressWarnings("serial")
public class TimeSeriesEnsemble extends LinkedList<TimeSeries> {
    private int agentId;
    private Brain brain;

    public TimeSeriesEnsemble(int agentId, Brain brain) {
        this.agentId = agentId;
        this.brain = brain;
    }

    public int getAgentId() {
        return agentId;
    }

    public Brain getBrain() {
        return brain;
    }

    public boolean add(TimeSeries observations) {
        assert observations.getDimension() == brain.getNeuronCount();
        return super.add(observations);
    }

    public TimeSeries concatenate() {
        if (size() <= 1) {
            return peek();
        }
        return stream().flatMap(TimeSeries::stream)
                .collect(Collectors.toCollection(() -> new TimeSeries(brain.getNeuronCount())));
    }
}
