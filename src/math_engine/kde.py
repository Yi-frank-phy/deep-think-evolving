
import numpy as np
from typing import Optional, Tuple

def compute_pairwise_dist_sq(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise squared Euclidean distances efficiently using matrix multiplication.

    dist_sq[i, j] = ||x_i - x_j||^2
    """
    dot_product = np.dot(embeddings, embeddings.T)
    sq_norm = np.diag(dot_product)
    dist_sq = sq_norm[:, np.newaxis] + sq_norm[np.newaxis, :] - 2 * dot_product
    return np.maximum(dist_sq, 0.0)

def estimate_bandwidth(
    embeddings: np.ndarray,
    precomputed_dist_sq: Optional[np.ndarray] = None
) -> float:
    """
    高维自适应带宽估计。
    
    对于 D >> N 的高维情况，传统 Silverman 规则失效。
    采用基于实际距离尺度的估计:
    
    h = median(pairwise_distances) / sqrt(2)
    
    这确保 ||u||²/(2h²) ≈ 1 对于典型距离，使 log_density 在合理范围内。
    
    Args:
        embeddings: (N, D) array of embedding vectors.
        precomputed_dist_sq: Optional (N, N) array of squared distances to avoid recomputation.
        
    Returns:
        Estimated bandwidth h.
    """
    embeddings = np.asarray(embeddings, dtype=float)
    if embeddings.ndim == 1:
        embeddings = embeddings[np.newaxis, :]
    
    N, D = embeddings.shape
    
    # 边界情况
    if N <= 1:
        return 1.0
    
    if precomputed_dist_sq is not None:
        dist_sq = precomputed_dist_sq
    else:
        dist_sq = compute_pairwise_dist_sq(embeddings)
    
    # 提取上三角 (不含对角线) 的距离
    upper_tri_indices = np.triu_indices(N, k=1)
    distances = np.sqrt(dist_sq[upper_tri_indices])
    
    if len(distances) == 0:
        return 1.0
    
    # 使用中位距离作为尺度参数
    median_dist = np.median(distances)
    
    # 避免零带宽
    if median_dist < 1e-10:
        # 回退到基于 L2 范数的估计
        # Note: We need sq_norm for this fallback if we want to be exact to original,
        # but using mean(sqrt(dist_sq)) over off-diagonals is a good enough approximation for "avg_norm" scale if centered
        # or we can just compute it if needed. For now let's stick to simple fallback logic to avoid complexity.
        return 1e-3
    
    # h = median_dist / sqrt(2) 确保典型距离下 exp(-d²/(2h²)) ≈ exp(-1)
    h = median_dist / np.sqrt(2)
    
    return float(h)

def gaussian_kernel_log_density(
    embeddings: np.ndarray, 
    bandwidth: float = 1.0, 
    epsilon: float = 1e-9,
    precomputed_dist_sq: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Computes the log probability density of each embedding given the population 
    using a Parzen-Rosenblatt Window with a Gaussian kernel.
    
    Args:
        embeddings: (N, D) array of embedding vectors.
        bandwidth: Scalar bandwidth parameter h.
        epsilon: Small constant to avoid numerical errors.
        precomputed_dist_sq: Optional (N, N) array of squared distances.
        
    Returns:
        (N,) array comprising the log-density estimate for each input embedding.
    """
    embeddings = np.asarray(embeddings, dtype=float)
    if embeddings.ndim == 1:
        embeddings = embeddings[np.newaxis, :]
        
    N, D = embeddings.shape
    if N == 0:
        return np.array([])
    
    # Warn about unreliable KDE in high dimensions with few samples
    if D > 100 and N < D:
        import warnings
        warnings.warn(
            f"KDE in {D} dimensions with only {N} samples may be unreliable. "
            f"Consider dimensionality reduction or alternative density estimation.",
            UserWarning
        )
    
    if precomputed_dist_sq is not None:
        dist_sq = precomputed_dist_sq
    else:
        dist_sq = compute_pairwise_dist_sq(embeddings)
    
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

def compute_kde_optimized(embeddings: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Optimized function to compute both bandwidth and log densities
    using a single distance matrix calculation.

    Returns:
        (bandwidth, log_densities)
    """
    dist_sq = compute_pairwise_dist_sq(embeddings)
    bandwidth = estimate_bandwidth(embeddings, precomputed_dist_sq=dist_sq)
    log_densities = gaussian_kernel_log_density(embeddings, bandwidth=bandwidth, precomputed_dist_sq=dist_sq)
    return bandwidth, log_densities
