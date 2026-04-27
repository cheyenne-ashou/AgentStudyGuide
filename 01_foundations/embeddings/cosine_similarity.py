"""
Cosine Similarity from Scratch
Pure math — no ML libraries. Shows how vectors represent meaning and how
cosine similarity measures semantic closeness regardless of vector magnitude.

Cosine similarity = dot(A, B) / (|A| * |B|)
  = 1.0  →  identical direction (same concept)
  = 0.0  →  orthogonal (unrelated concepts)
  = -1.0 →  opposite direction

Why cosine over Euclidean distance?
  Cosine is magnitude-invariant — a short doc and a long doc about the same
  topic will have the same cosine similarity even if their raw vectors differ.

Run: python 01_foundations/embeddings/cosine_similarity.py
"""
import math


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def magnitude(v: list[float]) -> float:
    return math.sqrt(sum(x ** 2 for x in v))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    mag = magnitude(a) * magnitude(b)
    return 0.0 if mag == 0 else dot_product(a, b) / mag


def euclidean_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# Hand-crafted 4-dimensional vectors
# Dimensions: [is_animal, is_domestic, is_software, is_query_language]
CONCEPTS = {
    "dog":          [0.9, 0.85, 0.0, 0.0],
    "cat":          [0.85, 0.9, 0.0, 0.0],
    "wolf":         [0.9, 0.1, 0.0, 0.0],
    "python_snake": [0.7, 0.05, 0.1, 0.0],
    "python_lang":  [0.0, 0.0, 0.9, 0.8],
    "sql":          [0.0, 0.0, 0.7, 0.95],
}


def print_similarity_matrix():
    names = list(CONCEPTS.keys())
    vecs = list(CONCEPTS.values())
    width = max(len(n) for n in names)
    header = " " * (width + 2) + "  ".join(f"{n[:8]:>8}" for n in names)
    print(header)
    for i, (name_a, vec_a) in enumerate(zip(names, vecs)):
        row = f"{name_a:<{width}}  "
        for vec_b in vecs:
            sim = cosine_similarity(vec_a, vec_b)
            row += f"  {sim:>6.3f}"
        print(row)


if __name__ == "__main__":
    print("=== COSINE SIMILARITY DEMO ===\n")

    print("Vectors (4 dims: animal, domestic, software, query_lang):")
    for name, vec in CONCEPTS.items():
        print(f"  {name:<14} {vec}")

    print("\n--- Similarity Matrix ---")
    print_similarity_matrix()

    print("\n--- Query: 'pet animal' [0.8, 0.88, 0, 0] ---")
    query = [0.8, 0.88, 0.0, 0.0]
    results = sorted(
        [(name, cosine_similarity(query, vec)) for name, vec in CONCEPTS.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    for name, score in results:
        bar = "█" * int(score * 20)
        print(f"  {name:<14} {score:.3f}  {bar}")

    print("\n--- Why magnitude-invariance matters ---")
    short = [0.9, 0.85, 0.0, 0.0]   # same direction as dog, smaller magnitude
    long  = [9.0, 8.5, 0.0, 0.0]    # same direction, 10x larger
    dog   = CONCEPTS["dog"]
    print(f"  dog vector:        {dog}")
    print(f"  short dog vector:  {short}")
    print(f"  long dog vector:   {long}")
    print(f"  cosine(dog, short) = {cosine_similarity(dog, short):.3f}")
    print(f"  cosine(dog, long)  = {cosine_similarity(dog, long):.3f}")
    print(f"  euclidean(dog, short) = {euclidean_distance(dog, short):.3f}")
    print(f"  euclidean(dog, long)  = {euclidean_distance(dog, long):.3f}")
    print("\n  Cosine is the same for both — Euclidean is not.")
    print("  This is why we use cosine for semantic search.")
