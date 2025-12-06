
import numpy as np

def gaussian_kernel_log_density(
    embeddings: np.ndarray, 
    bandwidth: float = 1.0, 
    epsilon: float = 1e-9
) -> np.ndarray:
    """
    Computes the log probability density of each embedding given the population 
    using a Parzen-Rosenblatt Window with a Gaussian kernel.
    
    Args:
        embeddings: (N, D) array of embedding vectors.
        bandwidth: Scalar bandwidth parameter h.
        epsilon: Small constant to avoid numerical errors (not directly used in log domain usually, but kept for consistency).
        
    Returns:
        (N,) array comprising the log-density estimate for each input embedding.
    """
    embeddings = np.array(embeddings, dtype=float)
    if embeddings.ndim == 1:
        embeddings = embeddings[np.newaxis, :]
        
    N, D = embeddings.shape
    if N == 0:
        return np.array([])
    
    # Calculate squared Euclidean distances between all pairs
    # dist_sq[i, j] = ||x_i - x_j||^2
    # Expanding ||x - y||^2 = ||x||^2 + ||y||^2 - 2<x, y>
    
    dot_product = np.dot(embeddings, embeddings.T) # (N, N)
    sq_norm = np.diag(dot_product) # (N,)
    
    # dist_sq[i, j] = sq_norm[i] + sq_norm[j] - 2 * dot_product[i, j]
    dist_sq = sq_norm[:, np.newaxis] + sq_norm[np.newaxis, :] - 2 * dot_product
    
    # Avoid negative values due to numerical precision
    dist_sq = np.maximum(dist_sq, 0.0)
    
    # Log-Kernel value for each pair (unnormalized by 1/N yet)
    # log K_h(u) = - (d/2)log(2*pi) - d*log(h) - ||u||^2 / (2h^2)
    # Here u = x_i - x_j
    
    const_term = -0.5 * D * np.log(2 * np.pi) - D * np.log(bandwidth)
    log_kernels = const_term - dist_sq / (2 * bandwidth**2) # (N, N)
    
    # Now we need to compute log( (1/N) * sum_j exp(log_kernels[i, j]) )
    # = -log(N) + logsumexp_j(log_kernels[i, j])
    
    # Stable LogSumExp implementation
    max_log = np.max(log_kernels, axis=1) # (N,)
    # exp(log_k - max_log)
    exp_term = np.exp(log_kernels - max_log[:, np.newaxis])
    sum_exp = np.sum(exp_term, axis=1)
    
    log_density = -np.log(N) + max_log + np.log(sum_exp)
    
    return log_density

def estimate_density(embeddings: np.ndarray, bandwidth: float = 1.0) -> np.ndarray:
    """
    Wrapper to return probability density (exp(log_density)).
    Use with caution in high dimensions as p(x) might be extremely small.
    """
    log_p = gaussian_kernel_log_density(embeddings, bandwidth)
    return np.exp(log_p)
