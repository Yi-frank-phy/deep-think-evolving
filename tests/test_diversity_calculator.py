import numpy as np

from src.diversity_calculator import calculate_similarity_matrix


def test_calculate_similarity_matrix_with_valid_embeddings():
    strategies = [
        {"embedding": [1.0, 0.0, 0.0]},
        {"embedding": [0.0, 1.0, 0.0]},
        {"embedding": [1.0, 1.0, 0.0]},
    ]

    matrix = calculate_similarity_matrix(strategies)

    assert matrix.shape == (3, 3)
    assert np.isclose(matrix[0, 0], 1.0)
    assert np.isclose(matrix[1, 1], 1.0)
    # Orthogonal vectors should have similarity close to 0
    assert np.isclose(matrix[0, 1], 0.0, atol=1e-6)
    # Third vector equally aligned with first two -> similarity around 0.7071
    assert np.isclose(matrix[2, 0], 1 / np.sqrt(2), atol=1e-6)
    assert np.isclose(matrix[2, 1], 1 / np.sqrt(2), atol=1e-6)


def test_calculate_similarity_matrix_with_invalid_payload():
    assert calculate_similarity_matrix([]).size == 0
    assert calculate_similarity_matrix([{"no_embedding": []}]).size == 0


def test_calculate_similarity_matrix_with_mismatched_dimensions(capfd):
    strategies = [
        {"embedding": [1.0, 0.0, 0.0]},
        {"embedding": [0.0, 1.0]},
    ]

    matrix = calculate_similarity_matrix(strategies)

    assert matrix.size == 0
    captured = capfd.readouterr()
    assert "inconsistent dimensions" in captured.out


def test_calculate_similarity_matrix_with_empty_embedding(capfd):
    strategies = [
        {"embedding": []},
        {"embedding": [1.0, 0.0, 0.0]},
    ]

    matrix = calculate_similarity_matrix(strategies)

    assert matrix.size == 0
    captured = capfd.readouterr()
    assert "empty embedding" in captured.out
