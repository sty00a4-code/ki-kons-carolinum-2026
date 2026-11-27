"""Der Hungarian-Algorithmus gegen eine Brute-Force-Suche"""

import random

from app.services.hungarian import solve_max


def _brute_force(scores):
    rows, cols = len(scores), len(scores[0])
    best = 0.0

    def rec(i, used, total):
        nonlocal best
        if i == rows:
            best = max(best, total)
            return
        rec(i + 1, used, total)  # Zeile bleibt unzugeordnet
        for j in range(cols):
            if j not in used and scores[i][j] > 0:
                rec(i + 1, used | {j}, total + scores[i][j])

    rec(0, frozenset(), 0.0)
    return best


def test_matches_brute_force_on_random_matrices():
    rng = random.Random(1)
    for _ in range(500):
        rows, cols = rng.randint(1, 5), rng.randint(1, 6)
        scores = [
            [
                rng.choice([0, 0, rng.randint(1, 20), rng.random() * 10])
                for _ in range(cols)
            ]
            for _ in range(rows)
        ]
        pairs = solve_max(scores)
        assert len({i for i, _ in pairs}) == len(pairs)
        assert len({j for _, j in pairs}) == len(pairs)
        assert all(scores[i][j] > 0 for i, j in pairs)
        assert abs(sum(scores[i][j] for i, j in pairs) - _brute_force(scores)) < 1e-6


def test_beats_greedy_where_greedy_blocks_itself():
    # Greedy nähme (0,0)=10 und ließe Zeile 1 leer (Summe 10); optimal sind 9+9.
    assert solve_max([[10, 9], [9, 0]]) == [(0, 1), (1, 0)]


def test_empty_and_zero_matrices():
    assert solve_max([]) == []
    assert solve_max([[]]) == []
    assert solve_max([[0, 0], [0, 0]]) == []
