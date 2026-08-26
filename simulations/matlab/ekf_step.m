function [estimate, covariance, innovation, diagonal] = ekf_step( ...
    previousEstimate, previousCovariance, command, measurement, p)
if nargin < 5 || isempty(p)
    p = robot_parameters();
end
predicted = position_step(previousEstimate, command, p.dt, ...
    p.velocityTimeConstant);
[A, ~] = state_jacobian(previousEstimate, command, p.dt, ...
    p.velocityTimeConstant);
Q = diag(p.ekfProcessNoiseStd(:).^2);
R = diag(p.ekfMeasurementNoiseStd(:).^2);
predictedCovariance = A * previousCovariance * A' + Q;
innovation = double(measurement(:)) - predicted;
innovation(3) = wrap_angle(innovation(3));
S = predictedCovariance + R;
K = predictedCovariance / S;
estimate = predicted + K * innovation;
estimate(3) = wrap_angle(estimate(3));
I = eye(6);
covariance = (I - K) * predictedCovariance * (I - K)' + K * R * K';
covariance = 0.5 * (covariance + covariance');
diagonal = diag(covariance);
end
