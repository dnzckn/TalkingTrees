"""Counter Memory Demonstration

Shows the critical difference between memory=True and memory=False with counters.

Scenario: 3 counters under a Sequence, each counts to 10 then returns SUCCESS.

With memory=TRUE:  Counter1 counts to 10, then Counter2, then Counter3 → Total = 30
With memory=FALSE: Counter1 counts to 10, but then Counter2 returns RUNNING → restarts from Counter1!
                   Counter1 already succeeded, so moves to Counter2 again...

Let's see what actually happens!
"""

import time

from py_trees import behaviour, common, composites


class Counter(behaviour.Behaviour):
    """A counter that increments each tick until reaching target."""

    def __init__(self, name: str, target: int = 10):
        super().__init__(name=name)
        self.target = target
        self.count = 0

    def initialise(self):
        """Called when behaviour is first ticked."""
        self.logger.info(f"{self.name} initialised (count starts at {self.count})")

    def update(self) -> common.Status:
        """Increment counter each tick."""
        self.count += 1
        self.feedback_message = f"Count: {self.count}/{self.target}"

        if self.count >= self.target:
            self.logger.info(f"{self.name} COMPLETE! Counted to {self.count}")
            return common.Status.SUCCESS
        else:
            self.logger.info(f"{self.name} counting... {self.count}/{self.target}")
            return common.Status.RUNNING

    def terminate(self, new_status: common.Status):
        """Called when behaviour finishes or is interrupted."""
        self.logger.info(f"{self.name} terminated with status {new_status}")


def run_memory_demo(memory: bool):
    """Run the counter demo with specified memory setting."""

    print("\n" + "=" * 70)
    print(f"COUNTER DEMO: memory={memory}")
    print("=" * 70)

    # Create tree with 3 counters
    counter1 = Counter("Counter1", target=10)
    counter2 = Counter("Counter2", target=10)
    counter3 = Counter("Counter3", target=10)

    root = composites.Sequence(
        name="Count to 30", memory=memory, children=[counter1, counter2, counter3]
    )

    # Tick until complete (or give up after 50 ticks)
    tick_count = 0
    max_ticks = 50

    while tick_count < max_ticks:
        tick_count += 1
        root.tick_once()

        total_count = counter1.count + counter2.count + counter3.count
        print(f"\nTick {tick_count}: Status={root.status.value}")
        print(f"  Counter1: {counter1.count}/10 [{counter1.status.value}]")
        print(f"  Counter2: {counter2.count}/10 [{counter2.status.value}]")
        print(f"  Counter3: {counter3.count}/10 [{counter3.status.value}]")
        print(f"  TOTAL: {total_count}/30")

        if root.status == common.Status.SUCCESS:
            print(f"\n Tree completed in {tick_count} ticks!")
            print(f" Total count: {total_count}")
            break

        time.sleep(0.1)

    if root.status != common.Status.SUCCESS:
        total_count = counter1.count + counter2.count + counter3.count
        print(f"\n[X] Tree did NOT complete after {tick_count} ticks")
        print(f"[X] Total count: {total_count}/30")
        print(f"[X] This is why memory={memory} matters!")

    return tick_count, counter1.count + counter2.count + counter3.count


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# MEMORY PARAMETER DEMONSTRATION: 3 Counters")
    print("#" * 70)

    # Run with memory=True (should count to 30)
    ticks_true, total_true = run_memory_demo(memory=True)

    # Run with memory=False (should get stuck)
    ticks_false, total_false = run_memory_demo(memory=False)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"memory=True:  {ticks_true} ticks, total count = {total_true}/30")
    print(f"memory=False: {ticks_false} ticks, total count = {total_false}/30")
    print("\n" + "=" * 70)
    print("KEY INSIGHT:")
    print("=" * 70)
    print("With memory=False, when Counter2 returns RUNNING, the Sequence")
    print("restarts from Counter1. But Counter1's status is SUCCESS, so it")
    print("doesn't get re-ticked. The Sequence moves directly to Counter2 again.")
    print("\nSo memory=False doesn't prevent completion, it just means the")
    print("Sequence re-evaluates from the start each tick!")
    print("=" * 70)
