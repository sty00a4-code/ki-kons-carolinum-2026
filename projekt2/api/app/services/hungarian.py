"""Hungarian-Algorithmus für rechteckige Zuordnungsprobleme: O(n^2 * m) mit n <= m
Gesucht wird die Zuordnung mit dem GRÖSSTEN Gesamtwert, bei der jede Zeile und jede Spalte
höchstens einmal vorkommt.
"""

_EPS = 1e-9


def _min_cost_assignment(cost: list[list[float]]) -> list[int]:
    """Kosten-Minimierung für n Zeilen <= m Spalten. Gibt je Zeile die Spalte
    zurück (Potenzial-Variante mit kürzesten augmentierenden Pfaden)."""
    n, m = len(cost), len(cost[0])
    inf = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    owner = [0] * (m + 1)  # owner[j] = Zeile (1-basiert), die Spalte j hält
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        owner[0] = i
        j0 = 0
        minv = [inf] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = owner[j0], inf, 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                current = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if current < minv[j]:
                    minv[j], way[j] = current, j0
                if minv[j] < delta:
                    delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if owner[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            owner[j0] = owner[j1]
            j0 = j1
    result = [-1] * n
    for j in range(1, m + 1):
        if owner[j]:
            result[owner[j] - 1] = j - 1
    return result


def solve_max(scores: list[list[float]]) -> list[tuple[int, int]]:
    """Beste Zuordnung für eine Wertematrix (Zeilen x Spalten, beliebige Form).

    Gibt (zeile, spalte)-Paare zurück, die zusammen den größten Wert ergeben.
    Paare mit Wert <= 0 werden weggelassen: "nicht zuordnen" ist besser als
    eine nutzlose Zuordnung."""
    if not scores or not scores[0]:
        return []
    rows, cols = len(scores), len(scores[0])
    top = max(max(row) for row in scores)
    # Minimieren: Kosten = top - Wert (immer >= 0). Bei mehr Zeilen als Spalten
    # transponieren, der Algorithmus braucht n <= m.
    transposed = rows > cols
    if transposed:
        cost = [[top - scores[i][j] for i in range(rows)] for j in range(cols)]
    else:
        cost = [[top - scores[i][j] for j in range(cols)] for i in range(rows)]
    pairs = []
    for a, b in enumerate(_min_cost_assignment(cost)):
        i, j = (b, a) if transposed else (a, b)
        if scores[i][j] > _EPS:
            pairs.append((i, j))
    return sorted(pairs)
