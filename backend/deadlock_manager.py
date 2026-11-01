"""Deadlock handling for SkillSync (OS concept: deadlock).

Three techniques, one per classic strategy:

1. OrderedLockManager -> PREVENTION  (breaks "circular wait")
2. BankersAlgorithm   -> AVOIDANCE   (only grants requests that keep the system in a safe state)
3. WaitForGraph       -> DETECTION   (finds a cycle among waiting processes)
"""
import threading
from contextlib import contextmanager


class DeadlockError(Exception):
    pass


# ---------------------------------------------------------------------------
# 1. PREVENTION: global lock ordering
# ---------------------------------------------------------------------------
class OrderedLockManager:
    """Every lock gets a fixed rank. Locks are always taken in rank order,
    so a circular wait can never form (Coffman condition broken)."""

    def __init__(self):
        self._locks = {}
        self._guard = threading.Lock()

    def register(self, name):
        with self._guard:
            if name not in self._locks:
                self._locks[name] = (len(self._locks), threading.Lock())

    @contextmanager
    def acquire(self, *names, timeout=5):
        for n in names:
            self.register(n)
        ordered = sorted(set(names), key=lambda n: self._locks[n][0])
        taken = []
        try:
            for n in ordered:
                if not self._locks[n][1].acquire(timeout=timeout):
                    raise DeadlockError(f"Timed out waiting for lock '{n}'")
                taken.append(n)
            yield ordered
        finally:
            for n in reversed(taken):
                self._locks[n][1].release()


# ---------------------------------------------------------------------------
# 2. AVOIDANCE: Banker's algorithm
# ---------------------------------------------------------------------------
class BankersAlgorithm:
    """processes = teams, resources = e.g. [mentor slots, project slots, seats]."""

    def __init__(self, available, max_need, allocation):
        self.available = list(available)
        self.max_need = [list(row) for row in max_need]
        self.allocation = [list(row) for row in allocation]
        self._lock = threading.Lock()

    def _need(self, i):
        return [m - a for m, a in zip(self.max_need[i], self.allocation[i])]

    def _safe_sequence(self, available, allocation):
        work = list(available)
        finished = [False] * len(allocation)
        sequence = []
        progress = True
        while progress:
            progress = False
            for i in range(len(allocation)):
                if finished[i]:
                    continue
                need = [m - a for m, a in zip(self.max_need[i], allocation[i])]
                if all(n <= w for n, w in zip(need, work)):
                    work = [w + a for w, a in zip(work, allocation[i])]
                    finished[i] = True
                    sequence.append(i)
                    progress = True
        return (all(finished), sequence if all(finished) else [])

    def is_safe(self):
        with self._lock:
            return self._safe_sequence(self.available, self.allocation)

    def request(self, pid, req):
        """Returns (granted, reason). State changes only if granted."""
        with self._lock:
            if any(r > n for r, n in zip(req, self._need(pid))):
                return False, "Request exceeds the maximum claim"
            if any(r > a for r, a in zip(req, self.available)):
                return False, "Resources not available, must wait"

            new_available = [a - r for a, r in zip(self.available, req)]
            new_allocation = [list(row) for row in self.allocation]
            new_allocation[pid] = [a + r for a, r in zip(new_allocation[pid], req)]

            safe, _ = self._safe_sequence(new_available, new_allocation)
            if not safe:
                return False, "Unsafe state, request denied to avoid deadlock"

            self.available = new_available
            self.allocation = new_allocation
            return True, "Granted"

    def release(self, pid):
        with self._lock:
            self.available = [a + x for a, x in zip(self.available, self.allocation[pid])]
            self.allocation[pid] = [0] * len(self.available)


# ---------------------------------------------------------------------------
# 3. DETECTION: wait-for graph
# ---------------------------------------------------------------------------
class WaitForGraph:
    """Edge A -> B means 'A is waiting for a resource held by B'.
    A cycle in this graph means deadlock."""

    def __init__(self):
        self._edges = {}
        self._lock = threading.Lock()

    def add_wait(self, waiter, holder):
        with self._lock:
            self._edges.setdefault(waiter, set()).add(holder)

    def remove_wait(self, waiter, holder):
        with self._lock:
            self._edges.get(waiter, set()).discard(holder)

    def find_cycle(self):
        with self._lock:
            graph = {k: set(v) for k, v in self._edges.items()}

        WHITE, GREY, BLACK = 0, 1, 2
        color = {}
        path = []

        def dfs(node):
            color[node] = GREY
            path.append(node)
            for nxt in graph.get(node, ()):
                state = color.get(nxt, WHITE)
                if state == GREY:
                    return path[path.index(nxt):] + [nxt]
                if state == WHITE:
                    found = dfs(nxt)
                    if found:
                        return found
            path.pop()
            color[node] = BLACK
            return None

        for start in list(graph):
            if color.get(start, WHITE) == WHITE:
                found = dfs(start)
                if found:
                    return found
        return None