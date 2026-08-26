function measurement = sensor_model(state, time, p)
if nargin < 3 || isempty(p)
    p = robot_parameters();
end
frequency = [1.7; 2.1; 1.3; 2.7; 1.9; 2.3];
noise = p.sensorNoiseStd(:) .* sin(frequency * time + p.sensorNoisePhase(:));
measurement = double(state(:)) + noise;
measurement(3) = wrap_angle(measurement(3));
end
