function result = run_checks()
root = fileparts(mfilename("fullpath"));
addpath(root);
state = zeros(6, 1);
command = [0.3; 0.1; 0.2];
next = position_step(state, command, 0.05, 0.08);
assert(isequal(size(next), [6, 1]));
assert(all(isfinite(next)));
dynamicParameters = robot_parameters();
poseRate = kinematics(state, state(4:6), "world");
inverseVelocity = kinematics(state, poseRate, "body");
wheelInverse = kinematics(state, command, "inverse", dynamicParameters);
bodyRecovered = kinematics(state, wheelInverse, "forward", dynamicParameters);
acceleration = dynamics( ...
    state, command, [0.2; -0.1; 0.03], dynamicParameters);
loadedState = plant_step( ...
    state, command, 0.05, [0.2; -0.1; 0.03], dynamicParameters);
assert(isequal(size(poseRate), [3, 1]));
assert(norm(inverseVelocity - state(4:6)) <= 1.0e-12);
assert(norm(bodyRecovered - command) <= 1.0e-12);
assert(isequal(size(acceleration), [3, 1]));
assert(isequal(size(loadedState), [6, 1]));
assert(norm(loadedState - next) > 1.0e-8);
wheels = wheel_speeds(command, 0.05, 0.20, 0.20);
assert(isequal(size(wheels), [4, 1]));
config = simulation.nmpcConfig();
config = simulation.nmpcSimulationConfig(config);
assert(config.dt < config.velocityTimeConstant);
measurement = sensor_model(next, config.dt, config);
[estimate, covariance, innovation, covarianceDiagonal] = ekf_step( ...
    state, config.ekfInitialCovariance, command, measurement, config);
assert(isequal(size(measurement), [6, 1]));
assert(isequal(size(estimate), [6, 1]));
assert(isequal(size(covariance), [6, 6]));
assert(isequal(size(innovation), [6, 1]));
assert(isequal(size(covarianceDiagonal), [6, 1]));
assert(all(eig(covariance) > -1.0e-12));
assert(trace(covariance) < trace(config.ekfInitialCovariance));
headings = [0, 0.7, -1.2, pi - 0.25, -pi + 0.25];
jacobianResidual = 0;
for heading = headings
    terminal = nmpc_controller.terminalDesign(heading, config);
    assert(terminal.controllabilityRank == 6);
    [Afd, Bfd] = finite_jacobian(heading, config);
    jacobianResidual = max(jacobianResidual, ...
        max(abs(terminal.A - Afd), [], "all"));
    jacobianResidual = max(jacobianResidual, ...
        max(abs(terminal.B - Bfd), [], "all"));
    audit = nmpc_controller.terminalAudit(heading, config);
    assert(audit.passed);
    assert(audit.maximumCommandViolation <= config.constraintTolerance);
end
assert(jacobianResidual <= 1.0e-6);
shortStepConfig = config;
shortStepConfig.dt = 0.02;
assert(nmpc_controller.terminalAudit(0.4, shortStepConfig).passed);
saturatedLagConfig = config;
saturatedLagConfig.dt = 0.25;
assert(nmpc_controller.terminalAudit(0.4, saturatedLagConfig).passed);
wrapResidual = abs(wrap_angle( ...
    (pi - 1.0e-8) - (-pi + 1.0e-8)) + 2.0e-8);
assert(wrapResidual <= 1.0e-12);
invalidReference = struct( ...
    "states", zeros(6, 1), "commands", zeros(3, 1));
invalidCheck = nmpc_controller.referenceAdmissible( ...
    invalidReference, config);
assert(~invalidCheck.accepted && ~invalidCheck.shapeValid);
stationary = nmpc_controller.stationaryReference(zeros(6, 1), config);
fallback = nmpc_controller.evaluatePlan( ...
    zeros(6, 1), zeros(3, config.horizon), stationary, config);
invalidGate = nmpc_controller.admit( ...
    zeros(6, 1), invalidReference, fallback, config);
assert(~invalidGate.accepted);
assert(invalidGate.fallbackUsable);
assert(invalidGate.newResult.selectionSource == "rejected_reference");
invalidCommands = zeros(3, config.horizon);
invalidCommands(1, 1) = config.commandUpper(1) + 0.10;
invalidCommands(1, 2) = -(config.commandUpper(1) + 0.10);
invalidPlan = nmpc_controller.evaluatePlan( ...
    zeros(6, 1), invalidCommands, stationary, config);
assert(~invalidPlan.feasible);
assert(invalidPlan.violation >= 0.099);
terminal = nmpc_controller.terminalDesign(zeros(6, 1), config);
outsideValue = terminal.rho + 0.5 * config.constraintTolerance;
outsideState = zeros(6, 1);
outsideState(1) = sqrt(outsideValue / terminal.P(1, 1));
nearBoundaryPlan = nmpc_controller.evaluatePlan( ...
    outsideState, zeros(3, config.horizon), stationary, config);
assert(nearBoundaryPlan.violation > 0);
assert(nearBoundaryPlan.violation < config.constraintTolerance);
assert(~nearBoundaryPlan.feasible);
boundedConfig = config;
boundedConfig.stateLower = [-1; -1; -pi; -2; -2; -3];
boundedConfig.stateUpper = [1; 1; pi; 2; 2; 3];
outsideInitialConfig = boundedConfig;
outsideInitialConfig.controllerMode = "nominal_nmpc";
outsideInitial = zeros(6, 1);
outsideInitial(1) = 1.10;
outsideInitialPlan = nmpc_controller.evaluatePlan( ...
    outsideInitial, zeros(3, config.horizon), stationary, ...
    outsideInitialConfig);
assert(~outsideInitialPlan.feasible);
assert(outsideInitialPlan.violation >= 0.099);
terminalState = [0.99; 0; 0; 0; 0; 0];
boundedTerminal = nmpc_controller.terminalDesign( ...
    terminalState, boundedConfig);
support = sqrt(boundedTerminal.rho * ...
    diag(boundedTerminal.P \ eye(6)));
assert(all(terminalState - support >= ...
    boundedConfig.stateLower - config.constraintTolerance));
assert(all(terminalState + support <= ...
    boundedConfig.stateUpper + config.constraintTolerance));
baselineFeasible = true;
for mode = ["linear_mpc", "nominal_nmpc", "terminal_nmpc"]
    baselineConfig = config;
    baselineConfig.controllerMode = mode;
    baseline = nmpc_controller.solve( ...
        zeros(6, 1), stationary, baselineConfig, []);
    baselineFeasible = baselineFeasible && baseline.feasible;
end
assert(baselineFeasible);
[nonzeroShiftResidual, nonzeroShiftFeasible] = ...
    nonzero_shift_regression(config);
assert(nonzeroShiftFeasible);
assert(nonzeroShiftResidual < -1.0e-12);
closedLoop = simulation.run();
assert(closedLoop.evidenceScope == "nmpc_lyapunov_only");
assert(closedLoop.initialErrorNorm > 0);
assert(closedLoop.referenceResidual <= config.referenceTolerance);
assert(closedLoop.yawVariation <= config.referenceTolerance);
assert(closedLoop.maximumSelectionResidual <= 1.0e-9);
assert(closedLoop.maximumLyapunovResidual <= 1.0e-8);
assert(closedLoop.maximumCostIncrease <= 1.0e-9);
assert(closedLoop.maximumStateViolation <= config.constraintTolerance);
assert(closedLoop.maximumCommandViolation <= config.constraintTolerance);
assert(closedLoop.maximumWheelViolation <= config.constraintTolerance);
assert(closedLoop.maximumTerminalRatio <= 1 + config.constraintTolerance);
assert(closedLoop.deadlineMissCount == 0);
parityResidual = python_parity(root, config);
assert(parityResidual <= 1.0e-12);
result = struct( ...
    "passed", true, ...
    "evidenceScope", "nmpc_lyapunov_only", ...
    "nextState", next, ...
    "kinematicsRate", poseRate, ...
    "dynamicsAcceleration", acceleration, ...
    "loadedState", loadedState, ...
    "ekfCovarianceTrace", trace(covariance), ...
    "nominalAlpha", min(1, config.dt / config.velocityTimeConstant), ...
    "terminalAuditDirections", config.terminalAuditDirections, ...
    "wrapResidual", wrapResidual, ...
    "wheelPeakRadps", max(abs(wheels)), ...
    "jacobianResidual", jacobianResidual, ...
    "invalidReferenceRejected", ~invalidCheck.accepted, ...
    "inputBoundRejection", ~invalidPlan.feasible, ...
    "strictConstraintRejection", ~nearBoundaryPlan.feasible, ...
    "initialStateBoundRejection", ~outsideInitialPlan.feasible, ...
    "stateContainment", true, ...
    "baselineFeasible", baselineFeasible, ...
    "nonzeroShiftResidual", nonzeroShiftResidual, ...
    "nonzeroClosedLoop", closedLoop, ...
    "matlabPythonParityResidual", parityResidual);
disp(jsonencode(result));
end

function [residual, feasible] = nonzero_shift_regression(config)
reference = nmpc_controller.stationaryReference(zeros(6, 1), config);
terminal = nmpc_controller.terminalDesign(zeros(6, 1), config);
factor = chol(terminal.P, "lower");
direction = [1; -0.5; 0.4; 0.2; -0.3; 0.1];
direction = direction / norm(direction, 2);
state = 0.5 * sqrt(terminal.rho) * (factor' \ direction);
commands = zeros(3, config.horizon);
cursor = state;
for index = 1:config.horizon
    errorState = nmpc_controller.trackingError(cursor, zeros(6, 1));
    commands(:, index) = terminal.K * errorState;
    cursor = position_step( ...
        cursor, commands(:, index), config.dt, ...
        config.velocityTimeConstant);
end
plan = nmpc_controller.evaluatePlan(state, commands, reference, config);
shifted = nmpc_controller.shiftPlan(plan, reference, config);
firstError = nmpc_controller.trackingError(state, zeros(6, 1));
firstStage = firstError' * config.Q * firstError + ...
    commands(:, 1)' * config.R * commands(:, 1);
residual = shifted.cost - plan.cost + firstStage;
feasible = plan.feasible && shifted.feasible;
end

function residual = python_parity(root, config)
script = fullfile(root, "..", "python", "verify.py");
command = sprintf('python "%s" --vectors', script);
[status, output] = system(command);
if status ~= 0
    command = sprintf('python3 "%s" --vectors', script);
    [status, output] = system(command);
end
assert(status == 0, output);
data = jsondecode(output);
residual = 0;
for index = 1:numel(data.cases)
    item = data.cases(index);
    state = item.state(:);
    input = item.command(:);
    next = position_step(state, input, ...
        item.dt, item.velocityTimeConstant);
    [A, B] = state_jacobian(state, input, ...
        item.dt, item.velocityTimeConstant);
    wheels = wheel_speeds(input, config.wheelRadius, ...
        config.halfLength, config.halfWidth);
    residual = max([residual; ...
        max(abs(next - item.nextState(:))); ...
        max(abs(A - item.A), [], "all"); ...
        max(abs(B - item.B), [], "all"); ...
        max(abs(wheels - item.wheels(:)))]);
end
end

function [A, B] = finite_jacobian(theta, config)
state = [0; 0; theta; 0; 0; 0];
command = zeros(3, 1);
step = 1.0e-6;
A = zeros(6, 6);
B = zeros(6, 3);
for index = 1:6
    delta = zeros(6, 1);
    delta(index) = step;
    plus = position_step( ...
        state + delta, command, config.dt, config.velocityTimeConstant);
    minus = position_step( ...
        state - delta, command, config.dt, config.velocityTimeConstant);
    A(:, index) = (plus - minus) / (2 * step);
end
for index = 1:3
    delta = zeros(3, 1);
    delta(index) = step;
    plus = position_step( ...
        state, command + delta, config.dt, config.velocityTimeConstant);
    minus = position_step( ...
        state, command - delta, config.dt, config.velocityTimeConstant);
    B(:, index) = (plus - minus) / (2 * step);
end
end
