import java.util.function.*;

public class ArgumentParser implements AutoCloseable {
    private String usage;
    private String programName;
    private String[] args;
    private int argIndex;

    public ArgumentParser(String usage, String programName, String[] args) {
        this.usage = usage;
        this.programName = programName;
        this.args = args;
        if (args.length > 0) {
            String arg0 = args[0];
            if (arg0.equals("-h") || arg0.equals("--help")) {
                System.out.printf(usage, programName);
                System.exit(0);
            }
        }
    }

    public <T> T parse(Function<String, T> converter, Predicate<T> predicate, String message) {
        if (argIndex >= args.length) {
            fail();
            return null;
        }
        try {
            T argument = converter.apply(args[argIndex]);
            if (!predicate.test(argument)) {
                fail(message);
                return null;
            }
            argIndex++;
            return argument;
        } catch (Throwable e) {
            fail(e.toString());
            return null;
        }
    }

    public <T> T parse(Function<String, T> converter) {
        return parse(converter, argument -> true, null);
    }

    private void fail() {
        System.err.printf(usage, programName);
        System.exit(1);
    }

    private void fail(String message) {
        System.err.printf("%s: %s: %s%n", programName, args[argIndex], message);
        System.exit(1);
    }

    public void close() {
        if (argIndex != args.length) {
            fail();
        }
    }
}
