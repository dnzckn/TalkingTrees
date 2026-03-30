"""Tests for WP-13: Resource Arbitration."""

from talking_trees.resources.manager import ResourceManager


def test_acquire_release():
    rm = ResourceManager()
    rm.register_resource("satellite", capacity=1)

    assert rm.acquire("satellite", "exec-1")
    assert not rm.acquire("satellite", "exec-2")  # held

    rm.release("satellite", "exec-1")
    assert rm.acquire("satellite", "exec-2")  # now free


def test_capacity_semaphore():
    rm = ResourceManager()
    rm.register_resource("drones", capacity=3)

    assert rm.acquire("drones", "a")
    assert rm.acquire("drones", "b")
    assert rm.acquire("drones", "c")
    assert not rm.acquire("drones", "d")  # capacity full

    rm.release("drones", "a")
    assert rm.acquire("drones", "d")  # now available


def test_release_all():
    rm = ResourceManager()
    rm.register_resource("r1")
    rm.register_resource("r2")

    rm.acquire("r1", "exec-1")
    rm.acquire("r2", "exec-1")

    count = rm.release_all("exec-1")
    assert count == 2

    assert rm.acquire("r1", "exec-2")
    assert rm.acquire("r2", "exec-2")


def test_status():
    rm = ResourceManager()
    rm.register_resource("cam", capacity=2)
    rm.acquire("cam", "a")

    status = rm.status("cam")
    assert status["capacity"] == 2
    assert status["available"] == 1
    assert "a" in status["holders"]


def test_list_resources():
    rm = ResourceManager()
    rm.register_resource("r1")
    rm.register_resource("r2")

    assert set(rm.list_resources()) == {"r1", "r2"}


def test_competing_executions():
    rm = ResourceManager()
    rm.register_resource("satellite", capacity=1)

    assert rm.acquire("satellite", "exec-1")
    assert not rm.acquire("satellite", "exec-2")

    rm.release("satellite", "exec-1")
    assert rm.acquire("satellite", "exec-2")
