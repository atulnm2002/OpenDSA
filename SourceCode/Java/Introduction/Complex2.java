
public class Complex {
  private final double re;
  private final double im;

  public Complex(double re, double im) {
    this.re = re;
    this.im = im;
  }

  @Override public boolean equals(Object o) {
    if (o == this)
      return true;
    if (!(o instanceof Complex))
      return false;
    Complex c = (Complex) o;

    return Double.compare(re, c.re) == 0 &&
           Double.compare(im, c.im) == 0;
  }

  @Override public String toString() {
    String sign = im < 0 ? " - " : " + ";
    return "(" + re + sign + im + "i)";
  }

  public static void main(String[] args)
  {
    Complex a = Complex(1, 0);
    Complex b = Complex(1, 0);

    if (a.equals(b)) {
      System.out.println ("'a' equals 'b'.");
    } else {
      System.out.println ("'a' and 'b' are not equal.");
    }
    System.out.println ("'a' = " + a);
    System.out.println ("'b' = " + b);
}
