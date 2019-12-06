

double dotProduct(int *a, int *b, int N) {

    double result = 0;

    #pragma parallel default(none) shared(a, b, N) private(i) reduction(+: result)
    for (int i = 0; i < N; i++) {
        result += a[i] * b[i];
    }
    return result;
}


int main() {



}