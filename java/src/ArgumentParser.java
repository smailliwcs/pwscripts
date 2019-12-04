import java.util.function.*;

public class ArgumentParser implements AutoCloseable {
    private String programName;
    private String[] args;
    private String[] argNames;
    private int argIndex = -1;

    public ArgumentParser(String[] args, String programName, String... argNames) {
        this.args = args;
        this.programName = programName;
        this.argNames = argNames;
        if (args.length != argNames.length) {
            fail();
        }
    }

    public String getUsage() {
        return String.format("Usage: %s %s%n", programName, String.join(" ", argNames));
    }

    public <T> T parse(Function<String, T> converter, Predicate<T> predicate, String message) {
        try {
            ++argIndex;
            if (argIndex >= args.length) {
                fail();
                return null;
            }
            T argument = converter.apply(args[argIndex]);
            if (!predicate.test(argument)) {
                fail(message);
                return null;
            }
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
        System.err.print(getUsage());
        System.exit(1);
    }

    private void fail(String message) {
        System.err.printf("%s: %s: %s%n", programName, args[argIndex], message);
        System.exit(1);
    }

    public void close() {
        if (argIndex == args.length - 1) {
            return;
        }
        System.err.print(getUsage());
        System.exit(1);
    }
}
