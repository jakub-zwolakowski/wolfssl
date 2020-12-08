
typedef unsigned short word16;

static void idea_mult(word16 x, word16 y)
{
    long mul;
    mul = (long)x * (long)y;
}

static void long_long_idea_mult(word16 x, word16 y)
{
    long mul;
    mul = (long long)x * (long long)y;
}

int main(void) {
    word16 x, y;
    x = 65361;
    y = 56540;
    long_long_idea_mult(x, y);
    idea_mult(x, y);
    return 0;
}
