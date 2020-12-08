
#include "time.h"
#include "string.h"

/* The libc 'time' function stub. */
time_t time(time_t *timer) {
  return 99;
}

/* The libc 'chdir' function stub. Does not work. */
int chdir(const char *path) {
  return 0;
}

/* The libc 'gmtime_r' function stub. */
struct tm *gmtime_r (const time_t *t, struct tm *tp) {
  memset(tp, 0, sizeof(struct tm));
  tp->tm_sec = 0;      /* Seconds. [0-60]      */
  tp->tm_min = 0;      /* Minutes. [0-59]      */
  tp->tm_hour = 0;     /* Hours.   [0-23]      */
  tp->tm_mday = 1;     /* Day.     [1-31]      */
  tp->tm_mon = 0;      /* Month.   [0-11]      */
  tp->tm_year = 0;     /* Year - 1900.         */
  tp->tm_wday = 0;     /* Day of week. [0-6]   */
  tp->tm_yday = 0;     /* Days in year.[0-365] */
  tp->tm_isdst = 0;    /* DST.     [-1/0/1]    */
  tp->tm_gmtoff = 0;   /* offset from UTC in seconds */
  tp->tm_zone = "UTC"; /* timezone abbreviation */
  return tp;
}
