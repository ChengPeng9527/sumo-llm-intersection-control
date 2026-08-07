# Simulation Assumptions

## Confirmed SUMO Context

- The simulated network is an unsignalized four-way intersection centered at `(-43.65, 11.26)`.
- The intersection node in the network is `J4`.
- The four controlled route directions are `N_S`, `S_N`, `E_W`, and `W_E`.
- The route conflict matrix is explicitly defined in `config/route_conflicts.yaml`.

## Lane Layout

The network file shows four inbound and four outbound approaches, each with four lanes on the main approaches.

### Inbound edges

- `N`
- `S`
- `E`
- `W`

### Outbound edges

- `-N`
- `-S`
- `-E`
- `-W`

### Observation

The network is more than a single-lane toy intersection: it contains multiple lanes per approach and internal junction edges. However, the project controller currently reasons over route-level decisions rather than full lane-level traffic control.

## Vehicle Model

The scenario generator defines the vehicle type as:

- length: `5`
- accel: `2.6`
- decel: `4.5`
- sigma: `0.5`
- maxSpeed: `13.89`

## Simulation Parameters

- simulation step length: `1.0 s`
- control radius: `45`
- stop speed threshold: `0.1`
- TTC threshold: `3.0 s`
- default simulation duration: `200 s`

## Arrival Generation

Scenario generation currently uses:

- route distributions defined by density,
- seed-based random route selection,
- integer departure gaps sampled between density-specific minimum and maximum values,
- scenario-specific route files generated under `simulation/generated_routes/`.

## Density Definitions

### low

- vehicles per hour: `120`
- duration: `240 s`
- route distribution: uniform over the four route ids
- minimum depart gap: `4`
- maximum depart gap: `12`

### medium

- vehicles per hour: `240`
- duration: `240 s`
- route distribution: uniform over the four route ids
- minimum depart gap: `2`
- maximum depart gap: `8`

### high

- vehicles per hour: `360`
- duration: `240 s`
- route distribution: uniform over the four route ids
- minimum depart gap: `1`
- maximum depart gap: `4`

## Random Seed Handling

- The scenario generator uses a seed-specific random number generator.
- The repository currently lists seeds `1` through `5` for formal experiment planning.
- The existing evidence files include seed `1` runs.

## Episode Termination

The episode ends when the configured simulation loop completes or when the run logic stops naturally after the planned step count.

## SUMO Native Behaviour

SUMO still controls:

- vehicle dynamics,
- car-following,
- lane geometry,
- internal junction behavior,
- collision avoidance outside the controller's direct action logic.

## Project-Controlled Behaviour

The project currently controls:

- high-level action selection,
- outside-control-zone FREE enforcement,
- cooperative WAIT-to-PROCEED promotion,
- deterministic safety downgrades,
- logging of raw, validated, postprocessed, and final decisions.

## Right-of-Way Interpretation

The project does not replace SUMO's physics or network geometry. It overlays a decision layer that chooses among `PROCEED`, `WAIT`, and `FREE`, then lets SUMO execute the resulting control command.

## Blocker Check

The current repository can explain the control logic and the route conflict matrix, but some historical result directories are not internally consistent in their metadata. Those runs should be treated as historical evidence only, not as clean dissertation-grade simulation assumptions.
