#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 100


int main()
{
  double a[N], b[N], result;
  int i;

  srand(time(0));

  for (i = 0; i < N; i++)
  {
    a[i] = ((double) rand())/((double) RAND_MAX);
    b[i] = ((double) rand())/((double) RAND_MAX);
  }

  for (i = 0; i < N; i++)
  {
    result += (a[i] * b[i]);
  }

  // Should be close to 25
  printf("result = %f\n", result);

  return 0;

}
