"""Engine C golden tests."""

import pytest
from dominant_circuit import (
    dispatch, InputContract, Job, Horizon,
    NonMarkovProcess,
)
from dominant_circuit.engines.sequential import belief_update, value_iteration


def test_belief_normalization():
    prior = {"s1": 0.5, "s2": 0.5}
    def obs_model(o, s):
        return 0.9 if s == "s1" else 0.2
    b = belief_update(prior, "o1", obs_model)
    assert abs(sum(b.values()) - 1.0) < 1e-10
    assert b["s1"] > b["s2"]


def test_belief_zero_likelihood_uniform():
    prior = {"s1": 0.7, "s2": 0.3}
    def obs_model(o, s):
        return 0.0
    b = belief_update(prior, "impossible", obs_model)
    assert abs(b["s1"] - 0.5) < 1e-10
    assert abs(b["s2"] - 0.5) < 1e-10


def test_value_iteration_toy():
    states = ["s0", "s1"]
    actions = ["stay", "go"]
    reward = {("s0", "stay"): 0.0, ("s0", "go"): 1.0, ("s1", "stay"): 2.0, ("s1", "go"): 0.0}
    transition = {
        ("s0", "stay"): {"s0": 1.0},
        ("s0", "go"): {"s1": 1.0},
        ("s1", "stay"): {"s1": 1.0},
        ("s1", "go"): {"s0": 1.0},
    }
    V, policy, residuals = value_iteration(states, actions, reward, transition, gamma=0.9)
    assert residuals[-1] < 1e-5
    assert policy["s1"] == "stay"


def test_non_markov_blocked():
    contract = InputContract(
        job=Job.SEQUENTIAL,
        horizon=Horizon.INFINITE_DISCOUNTED,
        gamma=0.9,
        markov_verified=False,
        states=["a"],
        actions=["x"],
        reward={("a", "x"): 1.0},
        transition={("a", "x"): {"a": 1.0}},
    )
    with pytest.raises(NonMarkovProcess):
        dispatch(Job.SEQUENTIAL, contract)


def test_mdp_dispatch():
    states = ["s0", "s1"]
    actions = ["stay", "go"]
    reward = {("s0", "stay"): 0.0, ("s0", "go"): 1.0, ("s1", "stay"): 2.0, ("s1", "go"): 0.0}
    transition = {
        ("s0", "stay"): {"s0": 1.0},
        ("s0", "go"): {"s1": 1.0},
        ("s1", "stay"): {"s1": 1.0},
        ("s1", "go"): {"s0": 1.0},
    }
    contract = InputContract(
        job=Job.SEQUENTIAL,
        horizon=Horizon.INFINITE_DISCOUNTED,
        gamma=0.9,
        markov_verified=True,
        states=states,
        actions=actions,
        reward=reward,
        transition=transition,
        tolerance=1e-8,
        k_max=500,
    )
    report = dispatch(Job.SEQUENTIAL, contract)
    assert report.decision["policy"]["s1"] == "stay"
    assert report.audit.passed
    assert "Bellman" in report.formula_name
