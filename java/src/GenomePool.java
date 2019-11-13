import java.util.*;

@SuppressWarnings("serial")
public class GenomePool extends HashMap<Integer, Genome> {
    private int time;
    private boolean dirty;

    public int getTime() {
        return time;
    }

    public void setTime(int time) {
        this.time = time;
    }

    public boolean isDirty() {
        return dirty;
    }

    public void setDirty(boolean dirty) {
        this.dirty = dirty;
    }
}
