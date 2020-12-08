
#define SZ 10

int main(void){
  int src[SZ] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
  int dst[SZ];
  int *dst_p = dst;
  int *src_p = src + SZ - 1;
  int i;
  for(i = 0; i < SZ; i++) {
    *dst_p++ = *src_p--;
  }
  return 0;
}
