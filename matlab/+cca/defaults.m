function cfg = defaults()
cfg.meta.version = "continuous-cca-ekf-0.2";
cfg.meta.provenance = "SIMULATION_NOMINAL_WITH_STM_GEOMETRY";
cfg.meta.seed = 27072026;

cfg.robot.wheelRadiusM = 0.100 / 2;
cfg.robot.halfLengthM = 0.156;
cfg.robot.halfWidthM = 0.176;
cfg.robot.gearRatio = 27;
cfg.robot.encoderCountsPerMotorRev = 4 * 500;

cfg.robot.massKg = 18.0;
cfg.robot.yawInertiaKgm2 = 1.25;
cfg.robot.wheelInertiaKgm2 = 0.002 * ones(4, 1);
cfg.robot.motorInertiaKgm2 = 1.0e-5 * ones(4, 1);
cfg.robot.viscousDamping = [10; 12; 1.8];
cfg.robot.coulombFriction = [2.0; 2.4; 0.4];
cfg.robot.frictionSmoothing = [0.08; 0.08; 0.10];

cfg.timing.sampleTimeS = 0.05;
cfg.timing.horizonSteps = 10;
cfg.timing.innerLoopPeriodS = 0.01;
cfg.timing.commandDelayS = 0.02;

cfg.position.maxSpeedMps = 0.65;
cfg.position.maxYawRateRadps = 1.40;
cfg.position.velocityTimeConstantS = 0.08;

cfg.control.mode = "position_state";
cfg.control.interface = "body_velocity";
cfg.control.stateDefinition = ["x", "y", "theta", "vx", "vy", "omega"];
cfg.control.commandDefinition = ["vx_cmd", "vy_cmd", "wz_cmd"];

cfg.actuator.torqueMinNm = -2.2 * ones(4, 1);
cfg.actuator.torqueMaxNm = 2.2 * ones(4, 1);
cfg.actuator.torqueRateMaxNmps = 12 * ones(4, 1);
cfg.actuator.wheelSpeedMaxRadps = 55 * ones(4, 1);
cfg.actuator.nmpcWheelSpeedBackoffRadps = 8 * ones(4, 1);
cfg.actuator.nmpcWheelSpeedBackoffProgress = [0, 0.75, 1];

cfg.plant.massScale = 1.10;
cfg.plant.yawInertiaScale = 0.90;
cfg.plant.viscousDampingScale = 1.20;
cfg.plant.coulombFrictionScale = 1.15;
cfg.plant.actuatorTimeConstantS = 0.04;
cfg.plant.commandDelayS = 0.02;
cfg.plant.integrationSubsteps = 5;

cfg.cost.Q = diag([20, 20, 8, 2, 2, 1]);
cfg.cost.R = 0.04 * eye(4);
cfg.cost.RDelta = 0.08 * eye(4);
cfg.cost.QTerminal = 10 * cfg.cost.Q;
cfg.cost.wheelSpeedTighteningWeight = 0.1;

cfg.controller.actuatorPredictionTimeConstantS = 0.08;
cfg.controller.commandDelaySamples = 1;

cfg.estimator.enabled = true;
cfg.estimator.measurementNoiseSeed = 27072028;
cfg.estimator.initialStd = [0.01; 0.01; deg2rad(0.3); 0.02; 0.02; 0.015];
cfg.estimator.processStdPerStep = [ ...
    5e-4; 5e-4; deg2rad(0.02); 0.01; 0.01; 0.008];
cfg.estimator.measurementStd = [ ...
    0.01; 0.01; deg2rad(0.3); 0.02; 0.02; 0.015];
cfg.estimator.covarianceFloor = 1e-12;

cfg.pid.poseKp = [1.4; 1.4; 1.2];
cfg.pid.poseKi = [0; 0; 0.04];
cfg.pid.velocityKp = [3.0; 3.0; 2.5];
cfg.pid.velocityMax = [0.8; 0.8; 0.8];
cfg.pid.integralLimit = [0.6; 0.6; 0.4];

cfg.risk.epsilonMin = 1.0e-4;
cfg.risk.barEpsilon = 0.050;
cfg.risk.contextBeta = 2.0;
cfg.risk.relaxationEnabled = false;
cfg.risk.relaxationWeight = 4.0e4;
cfg.risk.probabilityZeroToleranceM = 1.0e-10;

cfg.context.bias = -2.0;
cfg.context.weights = [2.0; 1.5; 1.0; 0.8; 0.6];
cfg.context.distanceScaleM = 2.0;
cfg.context.closingScaleMps = 1.0;
cfg.context.cpaTimeScaleS = 3.0;
cfg.context.calibrationValid = false;
cfg.context.calibrationHash = "";
cfg.context.calibrationDomain = "";
cfg.context.calibrationTailVerified = false;
cfg.context.frameTimeAgeVerified = false;
cfg.context.modePartitionVerified = false;
cfg.context.covarianceProvenanceVerified = false;
cfg.context.geometryContainmentVerified = false;
cfg.context.mode = "nominal";

cfg.safety.robotRadiusM = 0.32;
cfg.safety.humanEllipseSemiaxesM = [0.34; 0.26];
cfg.safety.clearanceM = 0.15;
cfg.safety.robotPositionStdM = 0.02;
cfg.safety.humanPositionStdM = 0.10;
cfg.safety.actuatorAuthorityFraction = 0.70;
cfg.safety.residualAccelerationBoundMps2 = 0.30;
cfg.safety.minimumNormalDistanceM = 1e-6;
cfg.safety.chanceVarianceFloorM2 = 1e-12;

cfg.solver.algorithm = "sqp";
cfg.solver.maxIterations = 40;
cfg.solver.maxFunctionEvaluations = 8000;
cfg.solver.constraintTolerance = 1e-6;
cfg.solver.optimalityTolerance = 1e-4;
cfg.solver.stepTolerance = 1e-8;
cfg.solver.display = "off";

cfg = studyDefaults(cfg);

cfg.terminal.slackScale = 0.25;
terminal = cca.Controllers.terminalIngredients(cfg);
cfg.cost.QTerminal = terminal.P;
cfg.terminal.rho = terminal.rho;
cfg.terminal.sampleCount = terminal.sampleCount;
cfg.terminal.decreaseTolerance = terminal.decreaseTolerance;
cfg.terminal.enforce = false;
validate(cfg);
end

function cfg = studyDefaults(cfg)
cfg.study.durationS = 6;
cfg.study.trajectoryDurationS = 10;
cfg.study.trajectoryPeriodS = 10;
cfg.study.trajectoryAmplitudeM = [1.0; 0.55];
cfg.study.settleBandFraction = 0.02;
cfg.study.openLoopStepWrench = [20; 0; 0];
cfg.study.openLoopChannelWrenches = diag([20, 20, 2]);
cfg.study.numericalParitySubsteps = 10;
cfg.study.zohParityTolerance = 1e-6;
cfg.study.numericalParityTolerance.oneStepStateError = 5e-7;
cfg.study.numericalParityTolerance.horizonStateError = 1e-6;
cfg.study.numericalParityTolerance.maximumPositionErrorM = 5e-7;
cfg.study.numericalParityTolerance.maximumYawErrorRad = 5e-7;
cfg.study.numericalParityTolerance.maximumVelocityError = 1e-6;
cfg.study.reference = [1.0; 0.6; pi / 6; 0; 0; 0];
cfg.study.goalToleranceM = 0.20;
cfg.study.goalYawToleranceRad = pi / 18;
cfg.study.goalVelocityTolerance = 0.10;
cfg.study.goalDwellS = 0.50;
cfg.study.plantMode = "nominal";
cfg.study.constantDisturbance = zeros(3, 1);
cfg.study.roaPositionRangeM = 0.8;
cfg.study.roaYawRangeRad = pi / 6;
cfg.study.roaGridPointsPerAxis = 5;
cfg.study.roaFinalPoseTolerance = 0.08;
cfg.study.roaFinalVelocityTolerance = 0.10;
end

function validate(cfg)
assert(cfg.control.mode == "position_state", ...
    "cca:config:ControlMode", ...
    "The active study uses six-state position control.");
assert(cfg.control.interface == "body_velocity", ...
    "cca:config:ControlInterface", ...
    "The active study sends body-velocity commands.");
assert(isequal(cfg.control.stateDefinition, ...
    ["x", "y", "theta", "vx", "vy", "omega"]));
assert(isequal(cfg.control.commandDefinition, ...
    ["vx_cmd", "vy_cmd", "wz_cmd"]));
positiveScalars = [
    cfg.robot.wheelRadiusM
    cfg.robot.halfLengthM
    cfg.robot.halfWidthM
    cfg.robot.massKg
    cfg.robot.yawInertiaKgm2
    cfg.timing.sampleTimeS
    cfg.timing.innerLoopPeriodS
];
assert(all(isfinite(positiveScalars) & positiveScalars > 0), ...
    "cca:config:Positive", "Positive parameters must be finite.");
assert(cfg.timing.horizonSteps >= 2 && ...
    cfg.timing.horizonSteps == floor(cfg.timing.horizonSteps));
assert(all(cfg.actuator.torqueMinNm < cfg.actuator.torqueMaxNm));
assert(all(cfg.actuator.torqueRateMaxNmps > 0));
assert(all(cfg.actuator.wheelSpeedMaxRadps > 0));
assert(all(cfg.actuator.nmpcWheelSpeedBackoffRadps >= 0));
assert(all(cfg.actuator.nmpcWheelSpeedBackoffRadps < ...
    cfg.actuator.wheelSpeedMaxRadps));
progress = cfg.actuator.nmpcWheelSpeedBackoffProgress;
assert(isrow(progress) && numel(progress) >= 2 && ...
    numel(progress) <= cfg.timing.horizonSteps);
assert(all(isfinite(progress)) && progress(1) == 0 && ...
    progress(end) == 1 && all(diff(progress) >= 0));
assert(all(eig(cfg.cost.Q) > 0) && all(eig(cfg.cost.R) > 0));
assert(isfinite(cfg.cost.wheelSpeedTighteningWeight) && ...
    cfg.cost.wheelSpeedTighteningWeight >= 0);
assert(isfinite(cfg.controller.actuatorPredictionTimeConstantS) && ...
    cfg.controller.actuatorPredictionTimeConstantS > 0);
assert(cfg.controller.commandDelaySamples == 1, ...
    "cca:config:ActuatorPrediction", ...
    "The certified reference implementation uses one command-delay sample.");
assert(cfg.estimator.enabled, "cca:config:EstimatorRequired", ...
    "The official CCA-NMPC study requires six-state EKF feedback.");
assert(numel(cfg.estimator.initialStd) == 6 && ...
    numel(cfg.estimator.processStdPerStep) == 6 && ...
    numel(cfg.estimator.measurementStd) == 6);
assert(all(isfinite(cfg.estimator.initialStd) & ...
    cfg.estimator.initialStd > 0));
assert(all(isfinite(cfg.estimator.processStdPerStep) & ...
    cfg.estimator.processStdPerStep > 0));
assert(all(isfinite(cfg.estimator.measurementStd) & ...
    cfg.estimator.measurementStd > 0));
assert(isfinite(cfg.estimator.covarianceFloor) && ...
    cfg.estimator.covarianceFloor > 0);
assert(cfg.estimator.measurementNoiseSeed >= 0 && ...
    cfg.estimator.measurementNoiseSeed == ...
    floor(cfg.estimator.measurementNoiseSeed));
assert(isfinite(cfg.risk.epsilonMin) && cfg.risk.epsilonMin >= 0);
assert(isfinite(cfg.risk.barEpsilon) && cfg.risk.barEpsilon > 0 && ...
    cfg.risk.barEpsilon < 0.5);
assert(isfinite(cfg.risk.contextBeta) && cfg.risk.contextBeta >= 0);
assert(islogical(cfg.risk.relaxationEnabled) && ...
    isscalar(cfg.risk.relaxationEnabled));
assert(isfinite(cfg.risk.relaxationWeight) && ...
    cfg.risk.relaxationWeight > 0);
assert(isfinite(cfg.risk.probabilityZeroToleranceM) && ...
    cfg.risk.probabilityZeroToleranceM >= 0);
assert(islogical(cfg.context.calibrationValid) && ...
    isscalar(cfg.context.calibrationValid));
assert(islogical(cfg.context.calibrationTailVerified) && ...
    isscalar(cfg.context.calibrationTailVerified));
assert(islogical(cfg.context.frameTimeAgeVerified) && ...
    isscalar(cfg.context.frameTimeAgeVerified));
assert(islogical(cfg.context.modePartitionVerified) && ...
    isscalar(cfg.context.modePartitionVerified));
assert(islogical(cfg.context.covarianceProvenanceVerified) && ...
    isscalar(cfg.context.covarianceProvenanceVerified));
assert(islogical(cfg.context.geometryContainmentVerified) && ...
    isscalar(cfg.context.geometryContainmentVerified));
assert(all(cfg.safety.humanEllipseSemiaxesM > 0));
assert(isfinite(cfg.safety.chanceVarianceFloorM2) && ...
    cfg.safety.chanceVarianceFloorM2 > 0);
assert(cfg.safety.actuatorAuthorityFraction > 0 && ...
    cfg.safety.actuatorAuthorityFraction <= 1);
assert(cfg.safety.residualAccelerationBoundMps2 >= 0);
assert(all(cfg.pid.poseKp > 0) && all(cfg.pid.poseKi >= 0));
assert(all(cfg.pid.velocityKp > 0) && all(cfg.pid.velocityMax > 0));
assert(all(cfg.pid.integralLimit > 0));
assert(cfg.study.roaGridPointsPerAxis >= 3 && ...
    mod(cfg.study.roaGridPointsPerAxis, 2) == 1);
assert(cfg.study.goalToleranceM > 0 && ...
    cfg.study.goalYawToleranceRad > 0 && ...
    cfg.study.goalVelocityTolerance > 0 && ...
    cfg.study.goalDwellS >= cfg.timing.sampleTimeS);
assert(cfg.study.trajectoryDurationS > 0 && ...
    cfg.study.trajectoryPeriodS > 0);
assert(numel(cfg.study.trajectoryAmplitudeM) == 2 && ...
    all(isfinite(cfg.study.trajectoryAmplitudeM) & ...
    cfg.study.trajectoryAmplitudeM > 0));
assert(cfg.study.numericalParitySubsteps >= 2 && ...
    cfg.study.numericalParitySubsteps == ...
    floor(cfg.study.numericalParitySubsteps));
assert(cfg.study.zohParityTolerance > 0);
parityLimits = struct2array(cfg.study.numericalParityTolerance);
assert(all(isfinite(parityLimits) & parityLimits > 0));
assert(cfg.terminal.slackScale > 0);
end
