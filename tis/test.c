
int printf(const char * restrict format, ... );

/* One macro to rule them all. */
#define MAKE_TEST(NAME) \
int NAME ## _test(void); \
int main_ ## NAME ## _test(void) { \
    int ret; \
    if ( (ret = NAME ## _test() ) == 0) { \
        printf("Test passed!\n"); \
    } else { \
        printf("Test failed: %d\n", ret); \
    }; \
    return ret; \
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
