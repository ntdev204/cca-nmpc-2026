function next = position_step(state, command, dt, velocityTimeConstant)
% Nominal discrete model used by the NMPC prediction.
state = double(state(:));
command = double(command(:));
alpha = min(1, double(dt) / double(velocityTimeConstant));
velocity = state(4:6) + alpha * (command - state(4:6));
next = state;
next(1:3) = state(1:3) + dt * kinematics(state, velocity, "world");
next(3) = wrap_angle(next(3));
next(4:6) = velocity;
end
