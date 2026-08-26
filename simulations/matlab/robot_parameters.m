function p = robot_parameters()
p.dt = 0.10;
p.velocityTimeConstant = 0.20;
p.lengthM = 0.40;
p.widthM = 0.40;
p.wheelRadius = 0.05;
p.halfLength = p.lengthM / 2;
p.halfWidth = p.widthM / 2;
p.footprintRadius = hypot(p.halfLength, p.halfWidth);
p.lidarHeightM = 0.24;
p.cameraHeightM = 0.20;
p.lidarFrontEdgeDistanceM = 0.10;
p.cameraFrontEdgeDistanceM = 0.035;
p.lidarPositionXM = 0.10;
p.cameraPositionXM = 0.165;
p.cameraPitchDeg = -20.0;
p.cameraPitchRad = deg2rad(p.cameraPitchDeg);
p.wheelSigns = [1; 1; 1; 1];
p.loadBodyAcceleration = [0.35; -0.25; 0.08];
p.sensorNoiseStd = [0.008; 0.008; 0.004; 0.030; 0.030; 0.020];
p.sensorNoisePhase = [0.20; 1.10; 2.00; 0.70; 1.70; 2.60];
p.ekfProcessNoiseStd = [0.004; 0.004; 0.002; 0.030; 0.030; 0.020];
p.ekfMeasurementNoiseStd = p.sensorNoiseStd;
p.ekfInitialCovariance = diag( ...
    [0.05; 0.05; 0.03; 0.15; 0.15; 0.10].^2);
end
