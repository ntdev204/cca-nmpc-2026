function [A, B] = state_jacobian(state, command, dt, velocityTimeConstant)
state = double(state(:));
command = double(command(:));
alpha = min(1, dt / velocityTimeConstant);
decay = 1 - alpha;
theta = state(3);
R = [cos(theta), -sin(theta), 0; ...
     sin(theta),  cos(theta), 0; ...
     0,           0,          1];
dR = [-sin(theta), -cos(theta), 0; ...
       cos(theta), -sin(theta), 0; ...
       0,           0,          0];
nextVelocity = decay * state(4:6) + alpha * command;
A = [eye(3), dt * decay * R; zeros(3), decay * eye(3)];
A(1:3, 3) = A(1:3, 3) + dt * dR * nextVelocity;
B = [dt * alpha * R; alpha * eye(3)];
end
