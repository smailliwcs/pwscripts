import java.io.*;

@SuppressWarnings("serial")
public class Genome {
    private byte[] genes;

    public Genome(int geneCount) {
        genes = new byte[geneCount];
    }

    public int get(int geneIndex) {
        return genes[geneIndex] & 0xff;
    }

    public void read(InputStream in) throws IOException {
        int offset = 0;
        while (true) {
            int count = in.read(genes, offset, genes.length - offset);
            if (count == -1) {
                throw new EOFException();
            }
            offset += count;
            if (offset == genes.length) {
                break;
            }
        }
    }
}
