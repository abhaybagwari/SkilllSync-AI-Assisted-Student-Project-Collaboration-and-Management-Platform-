
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from backend.deadlock_manager import (
    BankersAlgorithm,
    OrderedLockManager,
    WaitForGraph
)


def show_separator():
    print("\n" + "=" * 60)


def demo_deadlock_prevention():
    show_separator()
    print("1. DEADLOCK PREVENTION - ORDERED LOCKING")
    show_separator()

    manager = OrderedLockManager()

    print("Requesting locks in order: B, A")

    with manager.acquire("B", "A") as acquired:
        print("Actual acquisition order:", acquired)
        print("Both locks acquired successfully.")

    print("Locks released successfully.")


def demo_bankers_algorithm():
    show_separator()
    print("2. DEADLOCK AVOIDANCE - BANKER'S ALGORITHM")
    show_separator()

    available = [3, 3, 2]

    maximum = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]

    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]

    banker = BankersAlgorithm(
        available, maximum, allocation
    )

    print("Initial available resources:", banker.available)

    safe, sequence = banker.is_safe()

    print("\nInitial system state:")
    print("Safe:", safe)
    print("Safe sequence:", sequence)

    print("\nRequest 1: P1 requests [1, 0, 2]")

    granted, reason = banker.request(1, [1, 0, 2])

    print("Granted:", granted)
    print("Reason:", reason)
    print("Available after request:", banker.available)

    show_separator()
    print("3. UNSAFE REQUEST DEMONSTRATION")
    show_separator()

    banker2 = BankersAlgorithm(
        available, maximum, allocation
    )

    print("Request: P4 requests [3, 3, 1]")

    granted, reason = banker2.request(4, [3, 3, 1])

    print("Granted:", granted)
    print("Reason:", reason)
    print("Available after request:", banker2.available)
    print("Allocation unchanged:", banker2.allocation == allocation)


def demo_deadlock_detection():
    show_separator()
    print("4. DEADLOCK DETECTION - WAIT-FOR GRAPH")
    show_separator()

    graph = WaitForGraph()

    graph.add_wait("P1", "P2")
    graph.add_wait("P2", "P3")
    graph.add_wait("P3", "P1")

    print("Wait-for relationships:")
    print("P1 -> P2")
    print("P2 -> P3")
    print("P3 -> P1")

    cycle = graph.find_cycle()

    print("\nDetected cycle:", cycle)

    if cycle:
        print("DEADLOCK DETECTED!")

    print("\nRemoving one waiting relationship...")

    graph.remove_wait("P3", "P1")

    print("Cycle after removal:", graph.find_cycle())


def main():
    print("\nSKILLSYNC - OPERATING SYSTEM CONCEPT DEMONSTRATION")

    demo_deadlock_prevention()
    demo_bankers_algorithm()
    demo_deadlock_detection()

    show_separator()
    print("OS DEMONSTRATION COMPLETED")
    show_separator()


if __name__ == "__main__":
    main()
