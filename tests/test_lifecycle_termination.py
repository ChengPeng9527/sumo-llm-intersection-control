from common import resolve_sumo_termination_reason


class _FakeSimulation:
    def __init__(self, expected_sequence):
        self.expected_sequence = list(expected_sequence)
        self.calls = 0

    def getMinExpectedNumber(self):
        index = max(self.calls - 1, 0)
        index = min(index, len(self.expected_sequence) - 1)
        return self.expected_sequence[index]

class _FakeTraCI:
    def __init__(self, expected_sequence):
        self.simulation = _FakeSimulation(expected_sequence)
        self.step_calls = 0

    def simulationStep(self):
        self.step_calls += 1
        self.simulation.calls += 1


def test_resolve_sumo_termination_reason_all_vehicles_completed():
    reason = resolve_sumo_termination_reason(
        simulation_step=52,
        simulation_steps=400,
        expected_remaining=0,
        arrived_count=8,
        target_vehicle_count=8,
    )

    assert reason == 'ALL_VEHICLES_COMPLETED'


def test_resolve_sumo_termination_reason_sumo_no_expected_vehicles():
    reason = resolve_sumo_termination_reason(
        simulation_step=12,
        simulation_steps=400,
        expected_remaining=0,
        arrived_count=3,
        target_vehicle_count=8,
    )

    assert reason == 'SUMO_NO_EXPECTED_VEHICLES'


def test_resolve_sumo_termination_reason_max_horizon_reached():
    reason = resolve_sumo_termination_reason(
        simulation_step=399,
        simulation_steps=400,
        expected_remaining=2,
        arrived_count=6,
        target_vehicle_count=8,
    )

    assert reason == 'MAX_HORIZON_REACHED'


def test_controller_loop_stops_without_extra_simulation_step():
    fake = _FakeTraCI([3, 2, 1, 0])
    step = 0
    termination_reason = None

    while step < 10:
        fake.simulationStep()
        termination_reason = resolve_sumo_termination_reason(
            simulation_step=step,
            simulation_steps=10,
            expected_remaining=fake.simulation.getMinExpectedNumber(),
            arrived_count=4,
            target_vehicle_count=4,
        )
        if termination_reason:
            break
        step += 1

    assert fake.step_calls == 4
    assert termination_reason == 'ALL_VEHICLES_COMPLETED'
