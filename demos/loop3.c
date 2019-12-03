#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 100

int main()
{
  int i, j, k, len = N*N;
  double *a, *b, *c;
  a = malloc(len*sizeof(double));
  b = malloc(len*sizeof(double));
  c = malloc(len*sizeof(double));



  srand(time(0));

  for (i = 0; i < len; i++)
  {
    a[i] = ((double) rand())/((double) RAND_MAX);
    b[i] = ((double) rand())/((double) RAND_MAX);
  }

  for (i = 0; i < N; i++)
  {
    for (j = 0; j < N; j++)
    {
      c[i*N + j] = 0;
      for (k = 0; k < N; k++)
      {
        c[i*N+j] += (a[i*N+k] + b[k*N+j]);
      }
    }
  }

  for (i = 0; i < N; i++)
  {
    for (j = 0; j < N; j++)
    {
      printf("c[%d][%d] = %f\n", i, j, c[i*N+j]);
    }
  }

  free(a);
  free(b);
  free(c);

  return 0;

}
