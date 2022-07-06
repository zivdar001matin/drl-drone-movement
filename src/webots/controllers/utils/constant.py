# Constants, empirically found.
K_VERTICAL_THRUST = 68.5;  # with this thrust, the drone lifts.
K_VERTICAL_OFFSET = 0.6;   # Vertical offset where the robot actually targets to stabilize itself.
K_VERTICAL_P = 3.0;        # P constant of the vertical PID.
K_ROLL_P = 50.0;           # P constant of the roll PID.
K_PITCH_P = 30.0;          # P constant of the pitch PID.