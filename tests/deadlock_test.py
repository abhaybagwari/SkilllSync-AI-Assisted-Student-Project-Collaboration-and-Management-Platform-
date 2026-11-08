"""Tests and demo for backend/deadlock_manager.py

Run from the project root:
    python tests\\deadlock_test.py
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.deadlock_manager import (
    BankersAlgorithm, DeadlockError, OrderedLockManager, WaitForGraph,
)


def test_naive_locking_deadlocks():
    """Opposite lock order + both threads holding their first lock = deadlock."""
    a, b = threading.Lock(), threading.Lock()
    barrier = threading.Barrier(2)
    timed_out = []

    def worker(first, second):
        with first:
            barrier.wait()
            if not second.acquire(timeout=0.5):
                timed_out.append(True)
            else:
                second.release()

    t1 = threading.Thread(target=worker, args=(a, b))
    t2 = threading.Thread(target=worker, args=(b, a))
    t1.start(); t2.start(); t1.join(); t2.join()
    # Both threads wait on each other. The first to time out releases its lock,
    # which frees the other one, so at least one timeout proves the deadlock.
    assert len(timed_out) >= 1, "expected threads to get stuck (deadlock)"


def test_ordered_locks_prevent_deadlock():
    mgr = OrderedLockManager()
    mgr.register("project")
    mgr.register("mentor")
    done = []

    def worker(names):
        for _ in range(300):
            with mgr.acquire(*names, timeout=3):
                pass
        done.append(True)

    t1 = threading.Thread(target=worker, args=(("project", "mentor"),))
    t2 = threading.Thread(target=worker, args=(("mentor", "project"),))
    t1.start(); t2.start(); t1.join(10); t2.join(10)
    assert len(done) == 2, "threads did not finish, deadlock happened"


def test_ordered_lock_timeout_raises():
    mgr = OrderedLockManager()
    with mgr.acquire("x"):
        result = []

        def other():
            try:
                with mgr.acquire("x", timeout=0.2):
                    result.append("got it")
            except DeadlockError:
                result.append("timeout")

        t = threading.Thread(target=other)
        t.start(); t.join()
    assert result == ["timeout"]


def make_bankers():
    return BankersAlgorithm(
        available=[3, 3, 2],
        max_need=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
        allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
    )


def test_bankers_initial_state_is_safe():
    safe, seq = make_bankers().is_safe()
    assert safe is True
    assert seq == [1, 3, 4, 0, 2]


def test_bankers_grants_safe_request():
    granted, _ = make_bankers().request(1, [1, 0, 2])
    assert granted is True


def test_bankers_denies_unsafe_request():
    bank = make_bankers()
    bank.request(1, [1, 0, 2])
    granted, reason = bank.request(0, [0, 2, 0])
    assert granted is False
    assert "Unsafe" in reason


def test_bankers_denies_over_claim_and_unavailable():
    bank = make_bankers()
    assert bank.request(1, [9, 9, 9])[0] is False
    assert bank.request(4, [3, 3, 0])[0] is False


def test_bankers_release_frees_resources():
    bank = make_bankers()
    bank.release(2)
    assert bank.available == [6, 3, 4]


def test_wait_for_graph_detects_cycle():
    g = WaitForGraph()
    g.add_wait("Team1", "Team2")
    g.add_wait("Team2", "Team3")
    g.add_wait("Team3", "Team1")
    cycle = g.find_cycle()
    assert cycle is not None
    assert cycle[0] == cycle[-1]


def test_wait_for_graph_no_cycle():
    g = WaitForGraph()
    g.add_wait("Team1", "Team2")
    g.add_wait("Team2", "Team3")
    assert g.find_cycle() is None


def test_wait_for_graph_cycle_clears_after_release():
    g = WaitForGraph()
    g.add_wait("A", "B")
    g.add_wait("B", "A")
    assert g.find_cycle() is not None
    g.remove_wait("B", "A")
    assert g.find_cycle() is None
def test_bankers_rejects_negative_request():
    b = BankersAlgorithm(
        available=[3, 3],
        max_need=[[5, 5]],
        allocation=[[2, 2]]
    )

    try:
        b.request(0, [-1, 1])
        assert False, "Negative request was accepted"
    except ValueError:
        pass


def test_bankers_rejects_invalid_pid():
    b = BankersAlgorithm(
        available=[3, 3],
        max_need=[[5, 5]],
        allocation=[[2, 2]]
    )

    try:
        b.request(-1, [1, 1])
        assert False, "Invalid PID was accepted"
    except ValueError:
        pass


def test_bankers_rejects_wrong_vector_length():
    b = BankersAlgorithm(
        available=[3, 3],
        max_need=[[5, 5]],
        allocation=[[2, 2]]
    )

    try:
        b.request(0, [1])
        assert False, "Incorrect vector length was accepted"
    except ValueError:
        pass


def test_bankers_rejects_non_integer_request():
    b = BankersAlgorithm(
        available=[3, 3],
        max_need=[[5, 5]],
        allocation=[[2, 2]]
    )

    try:
        b.request(0, [1, "two"])
        assert False, "Non-integer request was accepted"
    except ValueError:
        pass


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)

