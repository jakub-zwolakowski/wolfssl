
extern int test_KO; /* Used to cause non-determinism if test fails. */

/* One macro to rule them all. */
#define MAKE_TEST_BIS(NAME) \
int NAME ## _test(void); \
int main_ ## NAME ## _test(void) { \
    if ( NAME ## _test() == 0) \
        return 0; \
    else \
        return test_KO; \
}

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
