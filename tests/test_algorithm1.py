import math

import pytest

from iscpp_simulator.simulation import compute_local_departure_times


def binary_delay(tau_1, tau_2):
    """tau_v(n) = tau_1 for n==1, tau_2 for n>=2 - the old binary delay model."""
    return lambda n: tau_1 if n <= 1 else tau_2


def test_single_agent_trivial():
    D = compute_local_departure_times(
        arrivals={1: 7}, wait_sets={}, delay_fn=binary_delay(10, 3)
    )
    assert D == {1: 17}


def test_two_agents_mutual_wait_matches_old_binary_formula():
    # Old two-agent condition (simulation.py, pre-generalization) operated on
    # t1/t2 that already included one solo-visit tau_1 (added when advancing
    # to the node), then "backed it out" in favor of tau_2:
    #   if abs(t2 - t1) < tau_1 - tau_2:
    #       t2 = max(t2, t1) - tau_1 + tau_2; t1 = t2
    # The new function takes raw arrival times (before any node delay), so
    # the bridge is old_t_i = arrival_i + tau_1.
    tau_1, tau_2 = 10, 4
    arrival_1, arrival_2 = 3, 5
    old_t1, old_t2 = arrival_1 + tau_1, arrival_2 + tau_1
    assert abs(old_t2 - old_t1) < tau_1 - tau_2
    old_merged = max(old_t1, old_t2) - tau_1 + tau_2

    D = compute_local_departure_times(
        arrivals={1: arrival_1, 2: arrival_2},
        wait_sets={1: frozenset({2}), 2: frozenset({1})},
        delay_fn=binary_delay(tau_1, tau_2),
    )
    assert D == {1: old_merged, 2: old_merged}


def test_two_agents_mutual_wait_not_beneficial_still_merges():
    # Explicit mutual wait is a binding commitment, independent of benefit -
    # only the *opportunistic* post-readiness extension is benefit-gated.
    tau_1, tau_2 = 5, 4
    D = compute_local_departure_times(
        arrivals={1: 0, 2: 100},
        wait_sets={1: frozenset({2}), 2: frozenset({1})},
        delay_fn=binary_delay(tau_1, tau_2),
    )
    assert D == {1: 104, 2: 104}


def test_unrequited_wait_is_indefinite():
    # a1 explicitly waits for a2; a2 and a3 mutually wait for each other and
    # form a tight, rigid pair that arrives well before a1 and has no
    # incentive to extend further (extending to a coalition of 3 only saves
    # 6->5, not worth waiting until t=5 for). a1's own closure requires
    # waiting for both a2 and a3 (transitively via a2), so once a2/a3 commit
    # to departing at t=6 without a1, a1's expectation is never honored and
    # it waits indefinitely.
    # NOTE: with only 2 agents, an unrequited explicit wait can never end up
    # indefinite - the paper's own text notes a later-ready agent always
    # weakly benefits from folding into an already-waiting coalition for
    # free, so it will always finalize alongside the waiter. Genuine
    # indefinite waits require >=3 agents, as here.
    delay = [10, 6, 5]
    delay_fn = lambda n: delay[min(n, len(delay)) - 1]
    D = compute_local_departure_times(
        arrivals={1: 5, 2: 0, 3: 0},
        wait_sets={
            1: frozenset({2}),
            2: frozenset({3}),
            3: frozenset({2}),
        },
        delay_fn=delay_fn,
    )
    assert D[2] == 6
    assert D[3] == 6
    assert D[1] == math.inf


def test_figure1_analogue_instability_and_indefinite_wait():
    arrivals = {1: 1, 2: 2, 3: 3, 4: 5}
    wait_sets = {
        1: frozenset({2, 4}),
        2: frozenset({3}),
        3: frozenset({2}),
        4: frozenset(),
    }
    delay = [10, 7, 6, 6]
    D = compute_local_departure_times(
        arrivals, wait_sets, delay_fn=lambda n: delay[min(n, len(delay)) - 1]
    )
    assert D[2] == 10
    assert D[3] == 10
    assert D[1] == math.inf
    assert D[4] == math.inf


def test_figure2_analogue_progressive_and_dominated_extension():
    arrivals = {1: 0, 2: 2, 3: 5, 4: 6, 5: 9, 6: 9}
    wait_sets = {
        1: frozenset({2}),
        2: frozenset({1}),
        3: frozenset(),
        4: frozenset(),
        5: frozenset(),
        6: frozenset(),
    }
    delay = [15, 10, 10, 5, 5, 5]
    D = compute_local_departure_times(
        arrivals, wait_sets, delay_fn=lambda n: delay[min(n, len(delay)) - 1]
    )
    assert D[1] == 11
    assert D[2] == 11
    assert D[3] == 11
    assert D[4] == 11
    assert D[5] == 19
    assert D[6] == 19


def test_wait_for_unknown_agent_raises():
    with pytest.raises(ValueError):
        compute_local_departure_times(
            arrivals={1: 0}, wait_sets={1: frozenset({2})}, delay_fn=binary_delay(5, 2)
        )


def test_readiness_time_ties_are_deterministic():
    delay = [8, 3, 3, 3]
    delay_fn = lambda n: delay[min(n, len(delay)) - 1]
    arrivals = {1: 5, 2: 5, 3: 5, 4: 5}
    wait_sets = {i: frozenset() for i in arrivals}
    D1 = compute_local_departure_times(arrivals, wait_sets, delay_fn)
    D2 = compute_local_departure_times(dict(arrivals), dict(wait_sets), delay_fn)
    assert D1 == D2
    # No explicit waits, but all arrive at the exact same instant with no
    # cost to pooling together: the opportunistic post-readiness extension
    # still merges all four for free (8 -> 3), since nobody has to wait any
    # longer than they already would alone. Explicit waiting sets are only
    # needed to *force* absorbing a not-yet-arrived agent at a real time
    # cost - simultaneous, already-present agents merge automatically
    # whenever it's beneficial, matching the paper's own text that a
    # later-ready coalition always weakly benefits from joining for free.
    assert D1 == {1: 8, 2: 8, 3: 8, 4: 8}


def test_no_departure_before_the_last_member_arrives():
    # Two pairs ready at 10 and four pairs ready at 20, tau falling to 10 at
    # 12 agents (an E1 lattice node). The first pair's pass extends its
    # coalition with everyone (departure 20 + tau(12) = 30); the second
    # pair's re-check must not use its own ready time 10 as the task start
    # (which gave departure 20, before the agents ready at 20 did any task).
    curve = [100, 92, 84, 75, 67, 59, 51, 43, 35, 26, 18, 10]
    arrivals = {1: 10, 10: 10, 4: 10, 7: 10, 0: 20, 2: 20, 3: 20, 11: 20, 5: 20, 9: 20, 6: 20, 8: 20}
    pairs = [(1, 10), (4, 7), (0, 2), (3, 11), (5, 9), (6, 8)]
    wait_sets = {a: {b} for x, y in pairs for a, b in ((x, y), (y, x))}
    D = compute_local_departure_times(arrivals, wait_sets, lambda n: curve[min(n, 12) - 1])
    assert D == {a: 30 for a in arrivals}
