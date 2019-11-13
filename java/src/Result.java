public class Result {
    private int count;
    private double sum;

    public int getCount() {
        return count;
    }

    public double getSum() {
        return sum;
    }

    public void add(double value) {
        count += 1;
        sum += value;
    }

    public void add(Result result) {
        count += result.count;
        sum += result.sum;
    }
}
