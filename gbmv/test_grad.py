import torch

import genbmm

device = torch.device("cuda:0")
#device = torch.device("cpu")

C = 8
K = 2

K1K = 2*K+1

# diagonal rep
bA = torch.randn(K1K, C, device=device)
x = torch.randn(C, device=device)

# dense
def band_to_dense(bA):
    K1K, C = bA.shape
    K = K1K // 2
    A = torch.zeros(C, C, device=device)
    # fill in diagonal of A
    for k in range(K):
        lenK = C - k
        # kth closest super diagonal
        diagonal = bA[K - k - 1]
        A.diagonal(k+1).copy_(diagonal[k+1:])

        # kth closest sub diagonal
        diagonal = bA[k-K]
        A.diagonal(-k-1).copy_(diagonal[k+1:])
    A.diagonal().copy_(bA[K])
    return A

def band_to_dense2(bA):
    K1K, C = bA.shape
    K = K1K // 2
    A = torch.zeros(C, C, device=device)
    for j in range(C):
        for i in range(max(0, j-K), min(C, j+K)):
            A[i,j] = bA[K+1+i-j, j]
    return A

A = band_to_dense(bA)
#y = A.T @ x # x @ A # really want this though
y = A @ x

A2 = band_to_dense2(bA)
y2 = A2 @ x

def clamp(x, l, u):
    return min(u, max(l, x))

# convert to C x K matrix
def band_to_rows(bA):
    K1K, C = bA.shape
    A = band_to_dense(bA)
    A_rows = torch.zeros(C, K1K, device=device)
    for c in range(C):
        lower = clamp(c-K, 0, C)
        upper = clamp(c+K+1, 0, C)
        length = upper - lower
        start = 0 if c >= K else K-c
        A_rows[c,start:start+length].copy_(A[c, lower:upper])
    return A_rows

xb = genbmm.BandedMatrix(x.view(1, C, 1), 0, 0)
Ab = genbmm.BandedMatrix(bA.view(1, C, K1K), K, K)
yb = xb.multiply(Ab).data.sum(2).squeeze()

# Ab.to_dense()
# Ab.data

def rows_to_dense(rA):
    C, K1K = rA.shape
    A = torch.zeros(C, C, device=device)
    for c in range(C):
        lower = clamp(c-K, 0, C)
        upper = clamp(c+K+1, 0, C)
        length = upper - lower
        start = 0 if c >= K else K-c
        #A_rows[c,:length].copy_(A[c, lower:upper])
        A[c,lower:upper] = rA[c,start:start+length]
    return A
rA = band_to_rows(bA)
A3 = rows_to_dense(rA)

import pdb; pdb.set_trace()
