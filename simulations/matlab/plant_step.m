function next = plant_step(state, command, dt, load, p)
if nargin < 5 || isempty(p)
    p = robot_parameters();
end
if nargin < 4 || isempty(load)
    load = zeros(3, 1);
end
[~, derivative] = dynamics(state, command, load, p);
next = double(state(:)) + double(dt) * derivative;
next(3) = wrap_angle(next(3));
end
