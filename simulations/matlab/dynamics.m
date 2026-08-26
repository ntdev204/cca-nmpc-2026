function [acceleration, derivative] = dynamics(state, command, load, p)
% First-order body-velocity dynamics with a constant load.
if nargin < 4 || isempty(p)
    p = robot_parameters();
end
state = double(state(:));
command = double(command(:));
load = double(load(:));
if numel(state) ~= 6 || numel(command) ~= 3 || numel(load) ~= 3
    error("dynamics:shape", "Use state(6), command(3), and load(3)");
end
velocity = state(4:6);
acceleration = (command - velocity) / p.velocityTimeConstant + load;
if nargout > 1
    derivative = [kinematics(state, velocity, "world"); acceleration];
end
end
