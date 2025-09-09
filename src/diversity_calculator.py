import numpy as np

def calculate_similarity_matrix(strategies: list[dict]) -> np.ndarray:
    """
    Calculates the pairwise cosine similarity matrix for a list of embedded strategies.

    Args:
        strategies: A list of strategy dictionaries, where each dictionary
                    must contain an 'embedding' key with a vector.

    Returns:
        A numpy.ndarray representing the N x N matrix of pairwise cosine
        similarities, where N is the number of strategies.
        Returns an empty array if the input is invalid.
    """
    if not strategies or 'embedding' not in strategies[0]:
        print("Error: Input is not a valid list of embedded strategies.")
        return np.array([])

    # Extract the embedding vectors into a numpy array
    embeddings = np.array([s['embedding'] for s in strategies])

    # Normalize each vector to unit length
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms

    # Calculate the cosine similarity matrix using a dot product
    # The dot product of two unit vectors is their cosine similarity
    similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)

    return similarity_matrix
