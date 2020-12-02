
static unsigned char negative(signed char b)
{
  return ((unsigned char)b) >> 7;
}

static void ge_select(signed char b)
{
  unsigned char bnegative = negative(b);
  unsigned char babs = b - (((-bnegative) & b) << 1);

  /*
  ub1.c:10:[kernel] warning: invalid LHS operand for left shift.
                    assert 0 ≤ (int)((int)(-((int)bnegative))&(int)b);
                    stack: ge_select :: ub1.c:25 <- main
  */
}

static void ge_select_OK(signed char b)
{
  unsigned char bnegative = negative(b);
  unsigned char babs = b - ((((unsigned char)(-bnegative)) & b) << 1);

  /* ... */
}

int main(void) {
  ge_select_OK(5); // Corrected version, simulating 1st callstack: OK
  ge_select_OK(-8); // Corrected version, simulating 2nd callstack: OK

  ge_select(5); // Original version, simulating 1st callstack: OK
  ge_select(-8); // Original version, simulating 2nd callstack: UB

  return 0;
}

/*

# WHAT HAPPENS?

Without the cast to `unsigned char` the result of `-bnegative` is promoted to
`int`. In that case the left operand of `<<` has value `-8` and behavior is
undefined.

When we add the cast, the left operand of `<<` has value `248` and everything
goes well: `babs` gets value `8` in the end.

# SOURCES

6.5.3.3 Unary arithmetic operators

https://cigix.me/c17#6.5.3.3.p3

> The result of the unary- operator is the negative of its (promoted) operand.
> The integer promotions are performed on the operand, and the result has the
> promoted type.

6.5.7 Bitwise shift operators

https://cigix.me/c17#6.5.7.p4

> If E1 has an unsigned type (...)
> If E1 has a signed type and nonnegative value (...)
> otherwise, the behavior is undefined."

*/
