function value = kinematics(state, velocity, mode, p)
% Mecanum forward/inverse wheel kinematics and frame transforms.
state = double(state(:));
velocity = double(velocity(:));
if nargin < 3
    mode = "world";
end
if nargin < 4 || isempty(p)
    p = robot_parameters();
end
if numel(state) ~= 6
    error("kinematics:state", "State must contain six values");
end
theta = state(3);
R = [cos(theta), -sin(theta), 0; ...
     sin(theta),  cos(theta), 0; ...
     0,           0,          1];
arm = p.halfLength + p.halfWidth;
inverseMatrix = [1, -1, -arm; ...
                 1,  1,  arm; ...
                 1,  1, -arm; ...
                 1, -1,  arm] / p.wheelRadius;
name = lower(string(mode));
if name == "forward"
    if numel(velocity) ~= 4
        error("kinematics:forward", "Forward kinematics needs four wheel rates");
    end
    value = pinv(inverseMatrix) * velocity;
elseif name == "inverse"
    if numel(velocity) ~= 3
        error("kinematics:inverse", "Inverse kinematics needs a body velocity");
    end
    value = inverseMatrix * velocity;
elseif name == "world"
    if numel(velocity) ~= 3
        error("kinematics:world", "World transform needs a body velocity");
    end
    value = R * velocity;
elseif name == "body"
    if numel(velocity) ~= 3
        error("kinematics:body", "Body transform needs a world velocity");
    end
    value = R' * velocity;
else
    error("kinematics:mode", "Use forward, inverse, world, or body");
end
end
