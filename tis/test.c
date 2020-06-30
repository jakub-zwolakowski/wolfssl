
#define MAKE_TEST(NAME) \
int NAME ## _test(void); \
int main_ ## NAME ## _test(void) { \
    return NAME ## _test(); \
}

MAKE_TEST(error)
MAKE_TEST(memory)
MAKE_TEST(base64)
MAKE_TEST(asn)
MAKE_TEST(random)
MAKE_TEST(md5)
MAKE_TEST(sha)
MAKE_TEST(sha224)
MAKE_TEST(sha256)
MAKE_TEST(sha384)
MAKE_TEST(sha512)
