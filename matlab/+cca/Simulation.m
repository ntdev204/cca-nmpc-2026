classdef Simulation
    methods (Static)
        function result = simulate(controller, target, cfg, initialState)
        %SIMULATE Closed-loop nominal regulation with one selected controller.
        
        if nargin < 4
            initialState = zeros(6, 1);
        end
        assert(isequal(size(initialState), [6, 1]) && all(isfinite(initialState)));
        controller = upper(string(controller));
        steps = round(cfg.study.durationS / cfg.timing.sampleTimeS);
        time = (0:steps) * cfg.timing.sampleTimeS;
        states = zeros(6, steps + 1);
        states(:, 1) = initialState;
        measurements = zeros(6, steps + 1);
        estimatedStates = zeros(6, steps + 1);
        estimationCovariance = zeros(6, 6, steps + 1);
        measurementNoise = cca.Estimator.measurementNoise(steps + 1, cfg);
        measurements(:, 1) = cca.Estimator.observe( ...
            states(:, 1), measurementNoise(:, 1));
        filter = cca.Estimator.initialize(measurements(:, 1), cfg);
        estimatedStates(:, 1) = filter.mean;
        estimationCovariance(:, :, 1) = filter.covariance;
        torques = zeros(4, steps);
        requestedTorques = zeros(4, steps);
        solveTime = nan(1, steps);
        success = nan(1, steps);
        fallback = nan(1, steps);
        constraintViolation = nan(1, steps);
        previous = zeros(4, 1);
        warmStart = [];
        plantState = [];
        design = cca.Controllers.designLqr(cfg);
        safety.active = false;
        integralPoseError = zeros(3, 1);
        
        for k = 1:steps
            estimated = estimatedStates(:, k);
            switch controller
                case "OPEN_LOOP"
                    requested = zeros(4, 1);
                case "LQR"
                    error = estimated - target;
                    error(3) = atan2(sin(error(3)), cos(error(3)));
                    requested = -design.K * error;
                case "PID"
                    poseError = target(1:3) - estimated(1:3);
                    poseError(3) = atan2(sin(poseError(3)), cos(poseError(3)));
                    integralPoseError = integralPoseError + ...
                        cfg.timing.sampleTimeS * poseError;
                    integralPoseError = min(cfg.pid.integralLimit, ...
                        max(-cfg.pid.integralLimit, integralPoseError));
                    requested = cca.Controllers.bodyPidTorque( ...
                        estimated, target, integralPoseError, cfg);
                case "NMPC"
                    fallback(k) = false;
                    reference = cca.ControlPrimitives.regulationReference( ...
                        target, cfg.timing.horizonSteps);
                    appliedTorque = cca.ControlPrimitives.currentAppliedTorque( ...
                        plantState, previous);
                    solution = cca.Nmpc.solveNmpc(estimated, reference, ...
                        previous, safety, "NONE", cfg, warmStart, appliedTorque);
                    solveTime(k) = solution.solveTimeS;
                    success(k) = solution.success;
                    constraintViolation(k) = solution.maxConstraintViolation;
                    if solution.success
                        requested = solution.firstTorque;
                        warmStart = solution.warmStart;
                    else
                        error = estimated - target;
                        error(3) = atan2(sin(error(3)), cos(error(3)));
                        requested = -design.K * error;
                        warmStart = [];
                        fallback(k) = true;
                    end
                otherwise
                    error("cca:control:Controller", ...
                        "Unknown controller %s.", controller);
            end
            requestedTorques(:, k) = requested;
            applied = cca.ControlPrimitives.limitTorque(requested, previous, cfg);
            torques(:, k) = applied;
            [states(:, k + 1), plantState] = cca.Plant.advance( ...
                states(:, k), applied, previous, plantState, cfg);
            filter = cca.Estimator.predict(filter, applied, cfg);
            measurements(:, k + 1) = cca.Estimator.observe( ...
                states(:, k + 1), measurementNoise(:, k + 1));
            filter = cca.Estimator.update(filter, measurements(:, k + 1), cfg);
            estimatedStates(:, k + 1) = filter.mean;
            estimationCovariance(:, :, k + 1) = filter.covariance;
            previous = applied;
        end
        
        result.controller = controller;
        result.timeS = time;
        result.states = states;
        result.measurements = measurements;
        result.estimatedStates = estimatedStates;
        result.estimationCovariance = estimationCovariance;
        result.stateEstimator = "EKF";
        result.torques = torques;
        result.requestedTorques = requestedTorques;
        result.solveTimeS = solveTime;
        result.solverSuccess = success;
        result.fallback = fallback;
        result.solverConstraintViolation = constraintViolation;
        result.target = target;
        end

        function result = simulateScenario(controller, scenario, cfg)
        %SIMULATESCENARIO Receding-horizon CCA-NMPC from six-state EKF feedback.
        
        controller = upper(string(controller));
        steps = round(cfg.study.durationS / cfg.timing.sampleTimeS);
        time = (0:steps) * cfg.timing.sampleTimeS;
        contextCount = size(scenario.contextPositionM, 2);
        states = zeros(6, steps + 1);
        measurements = zeros(6, steps + 1);
        estimatedStates = zeros(6, steps + 1);
        estimationCovariance = zeros(6, 6, steps + 1);
        measurementNoise = cca.Estimator.measurementNoise(steps + 1, cfg);
        measurements(:, 1) = cca.Estimator.observe( ...
            states(:, 1), measurementNoise(:, 1));
        filter = cca.Estimator.initialize(measurements(:, 1), cfg);
        estimatedStates(:, 1) = filter.mean;
        estimationCovariance(:, :, 1) = filter.covariance;
        torques = zeros(4, steps);
        solveTime = zeros(1, steps);
        success = true(1, steps);
        fallback = false(1, steps);
        constraintViolation = zeros(1, steps);
        previous = zeros(4, 1);
        warmStart = [];
        plantState = [];
        design = cca.Controllers.designLqr(cfg);
        
        for k = 1:steps
            estimated = estimatedStates(:, k);
            nominal = localNominal(estimated, previous, warmStart, cfg);
            robotCovariance = repmat( ...
                estimationCovariance(1:2, 1:2, k), ...
                1, 1, cfg.timing.horizonSteps);
            crossCovariance = zeros(2, 2, contextCount, ...
                size(scenario.modeVelocityMps, 2), cfg.timing.horizonSteps);
            safety = cca.Scenario.predict(scenario, time(k), nominal, cfg, ...
                robotCovariance, crossCovariance);
            [safety, strategy] = localControllerContract( ...
                controller, safety);
            reference = cca.ControlPrimitives.referenceHorizon( ...
                estimated, scenario.target, cfg.timing.horizonSteps);
            appliedTorque = cca.ControlPrimitives.currentAppliedTorque(plantState, previous);
            solution = cca.Nmpc.solveNmpc(estimated, reference, previous, ...
                safety, strategy, cfg, warmStart, appliedTorque);
            solveTime(k) = solution.solveTimeS;
            success(k) = solution.success;
            constraintViolation(k) = solution.maxConstraintViolation;
            if solution.success
                requested = solution.firstTorque;
                warmStart = solution.warmStart;
            else
                requested = localLqrFallback( ...
                    estimated, scenario.target, design);
                warmStart = [];
                fallback(k) = true;
            end
            applied = cca.ControlPrimitives.limitTorque(requested, previous, cfg);
            torques(:, k) = applied;
            [states(:, k + 1), plantState] = cca.Plant.advance( ...
                states(:, k), applied, previous, plantState, cfg);
            filter = cca.Estimator.predict(filter, applied, cfg);
            measurements(:, k + 1) = cca.Estimator.observe( ...
                states(:, k + 1), measurementNoise(:, k + 1));
            filter = cca.Estimator.update(filter, measurements(:, k + 1), cfg);
            estimatedStates(:, k + 1) = filter.mean;
            estimationCovariance(:, :, k + 1) = filter.covariance;
            previous = applied;
        end
        result.controller = controller;
        result.timeS = time;
        result.states = states;
        result.measurements = measurements;
        result.estimatedStates = estimatedStates;
        result.estimationCovariance = estimationCovariance;
        result.stateEstimator = "EKF";
        result.torques = torques;
        result.contextPositionM = scenario.contextPositionM;
        result.solveTimeS = solveTime;
        result.solverSuccess = success;
        result.fallback = fallback;
        result.solverConstraintViolation = constraintViolation;
        result.target = scenario.target;
        result.contextCalibrationValid = cfg.context.calibrationValid;
        result = cca.AnalysisTools.scenarioOutcome(result, scenario, cfg);
        function nominal = localNominal(state, previous, warmStart, cfg)
        N = cfg.timing.horizonSteps;
        if isempty(warmStart)
            nominalTorques = repmat(previous, 1, N);
            nominal = cca.Model.rollout(state, nominalTorques, zeros(3, 1), ...
                cfg.timing.sampleTimeS, cfg.robot);
        else
            [nominal, ~] = cca.ControlPrimitives.unpackDecision(warmStart, N);
            nominal(:, 1) = state;
        end
        end
        
        function [safety, strategy] = localControllerContract(controller, safety)
        if controller == "DETERMINISTIC"
            safety.active = false;
            strategy = "NONE";
        elseif ismember(controller, ["UNIFORM", "CCA_FIXED_BUDGET"])
            strategy = controller;
        else
            error("cca:control:ScenarioController", ...
                "Unknown scenario controller %s.", controller);
        end
        end
        
        function torque = localLqrFallback(state, target, design)
        error = state - target;
        error(3) = atan2(sin(error(3)), cos(error(3)));
        torque = -design.K * error;
        end
        
        end

        function result = simulateTrajectory(controller, cfg)
        %SIMULATETRAJECTORY Track a time-varying figure-eight from EKF feedback.
        
        controller = upper(string(controller));
        assert(ismember(controller, ["LQR", "NMPC"]));
        steps = round(cfg.study.trajectoryDurationS / cfg.timing.sampleTimeS);
        time = (0:steps) * cfg.timing.sampleTimeS;
        desired = cca.ControlPrimitives.trajectoryReference(time, cfg);
        states = zeros(6, steps + 1);
        states(:, 1) = desired(:, 1);
        measurements = zeros(6, steps + 1);
        estimatedStates = zeros(6, steps + 1);
        estimationCovariance = zeros(6, 6, steps + 1);
        measurementNoise = cca.Estimator.measurementNoise(steps + 1, cfg);
        measurements(:, 1) = cca.Estimator.observe( ...
            states(:, 1), measurementNoise(:, 1));
        filter = cca.Estimator.initialize(measurements(:, 1), cfg);
        estimatedStates(:, 1) = filter.mean;
        estimationCovariance(:, :, 1) = filter.covariance;
        
        torques = zeros(4, steps);
        solveTime = nan(1, steps);
        success = nan(1, steps);
        fallback = nan(1, steps);
        constraintViolation = nan(1, steps);
        previous = zeros(4, 1);
        warmStart = [];
        plantState = [];
        design = cca.Controllers.designLqr(cfg);
        safety.active = false;
        
        for k = 1:steps
            estimated = estimatedStates(:, k);
            horizonTime = time(k) + ...
                (0:cfg.timing.horizonSteps) * cfg.timing.sampleTimeS;
            reference = cca.ControlPrimitives.trajectoryReference(horizonTime, cfg);
            reference(3, :) = localAlignYaw(reference(3, :), estimated(3));
            switch controller
                case "LQR"
                    trackingError = localStateError(estimated, reference(:, 1));
                    requested = -design.K * trackingError;
                case "NMPC"
                    fallback(k) = false;
                    appliedTorque = cca.ControlPrimitives.currentAppliedTorque( ...
                        plantState, previous);
                    solution = cca.Nmpc.solveNmpc( ...
                        estimated, reference, previous, safety, "NONE", ...
                        cfg, warmStart, appliedTorque);
                    solveTime(k) = solution.solveTimeS;
                    success(k) = solution.success;
                    constraintViolation(k) = solution.maxConstraintViolation;
                    if solution.success
                        requested = solution.firstTorque;
                        warmStart = solution.warmStart;
                    else
                        trackingError = localStateError( ...
                            estimated, reference(:, 1));
                        requested = -design.K * trackingError;
                        warmStart = [];
                        fallback(k) = true;
                    end
            end
            applied = cca.ControlPrimitives.limitTorque(requested, previous, cfg);
            torques(:, k) = applied;
            [states(:, k + 1), plantState] = cca.Plant.advance( ...
                states(:, k), applied, previous, plantState, cfg);
            filter = cca.Estimator.predict(filter, applied, cfg);
            measurements(:, k + 1) = cca.Estimator.observe( ...
                states(:, k + 1), measurementNoise(:, k + 1));
            filter = cca.Estimator.update(filter, measurements(:, k + 1), cfg);
            estimatedStates(:, k + 1) = filter.mean;
            estimationCovariance(:, :, k + 1) = filter.covariance;
            previous = applied;
        end
        
        desired(3, :) = localAlignYaw(desired(3, :), states(3, 1));
        result.controller = controller;
        result.timeS = time;
        result.desiredStates = desired;
        result.states = states;
        result.measurements = measurements;
        result.estimatedStates = estimatedStates;
        result.estimationCovariance = estimationCovariance;
        result.stateEstimator = "EKF";
        result.torques = torques;
        result.solveTimeS = solveTime;
        result.solverSuccess = success;
        result.fallback = fallback;
        result.solverConstraintViolation = constraintViolation;
        function error = localStateError(state, reference)
        error = state - reference;
        error(3) = atan2(sin(error(3)), cos(error(3)));
        end
        
        function aligned = localAlignYaw(yaw, anchor)
        aligned = zeros(size(yaw));
        yawPrevious = anchor;
        for i = 1:numel(yaw)
            aligned(i) = yawPrevious + atan2( ...
                sin(yaw(i) - yawPrevious), cos(yaw(i) - yawPrevious));
            yawPrevious = aligned(i);
        end
        end
        
        end

        function result = simulatePosition(controller, target, cfg, initialState)
        if nargin < 4
            initialState = zeros(6, 1);
        end
        controller = upper(string(controller));
        assert(ismember(controller, ["MPC", "NMPC", "DWA", "MPPI", ...
            "CCA_NMPC"]));
        assert(isequal(size(target), [6, 1]) && all(isfinite(target)));
        assert(isequal(size(initialState), [6, 1]) && all(isfinite(initialState)));
        steps = round(cfg.study.durationS / cfg.timing.sampleTimeS);
        time = (0:steps) * cfg.timing.sampleTimeS;
        states = zeros(6, steps + 1);
        states(:, 1) = initialState;
        commands = zeros(3, steps);
        solveTime = zeros(1, steps);
        status = strings(steps, 1);
        fallback = false(steps, 1);
        previous = zeros(3, 1);
        rngState = rng;
        cleanupRng = onCleanup(@() rng(rngState));
        rng(double(cfg.meta.seed) + sum(double(char(controller))));
        for k = 1:steps
            tic;
            switch controller
                case "MPC"
                    command = localMpc(states(:, k), target, previous, cfg);
                    status(k) = "MPC_SUCCESS";
                case "NMPC"
                    [command, status(k)] = localNmpc(states(:, k), target, previous, cfg);
                case "DWA"
                    [command, status(k)] = localDwa(states(:, k), target, previous, cfg);
                case "MPPI"
                    [command, status(k)] = localMppi(states(:, k), target, previous, cfg);
                case "CCA_NMPC"
                    [command, status(k)] = localCca(states(:, k), target, previous, cfg);
                otherwise
                    error("cca:control:Controller", "Unknown controller %s.", controller);
            end
            commands(:, k) = command;
            states(:, k + 1) = cca.Model.positionStep( ...
                states(:, k), command, cfg.timing.sampleTimeS, ...
                cfg.position.velocityTimeConstantS);
            solveTime(k) = toc;
            previous = command;
        end
        positionError = states(1:2, :) - target(1:2);
        yawError = atan2(sin(states(3, :) - target(3)), ...
            cos(states(3, :) - target(3)));
        result.controller = controller;
        result.controlMode = "position_state";
        result.stateDefinition = ["x", "y", "theta", "vx", "vy", "omega"];
        result.commandDefinition = ["vx_cmd", "vy_cmd", "wz_cmd"];
        result.timeS = time;
        result.states = states;
        result.commands = commands;
        result.target = target;
        result.solveTimeS = solveTime;
        result.finalPositionErrorM = norm(positionError(:, end));
        result.positionRmseM = sqrt(mean(sum(positionError.^2, 1)));
        result.yawRmseRad = sqrt(mean(yawError.^2));
        result.meanCommandVariationNorm = mean(vecnorm(diff( ...
            [zeros(3, 1), commands], 1, 2)));
        result.status = status;
        result.fallback = fallback;
        result.contextMode = "not_supplied";
        result.benchmarkScope = "position_state_interface_smoke";
        clear cleanupRng

        function command = localMpc(state, goal, previousCommand, localCfg)
        lookahead = max(localCfg.timing.sampleTimeS, ...
            localCfg.timing.horizonSteps * localCfg.timing.sampleTimeS);
        nominal = localNominal(state, goal, lookahead, localCfg);
        command = localSlew(nominal, previousCommand, localCfg);
        end

        function [command, label] = localNmpc(state, goal, previousCommand, localCfg)
        nominal = localNominal(state, goal, localCfg.timing.sampleTimeS, localCfg);
        scales = [0.60, 0.80, 1.00, 1.20, 1.40];
        [command, ~] = localBestConstant(state, goal, previousCommand, nominal, ...
            scales, localCfg);
        label = "NMPC_SUCCESS";
        end

        function [command, label] = localDwa(state, goal, previousCommand, localCfg)
        speed = localCfg.position.maxSpeedMps;
        yawRate = localCfg.position.maxYawRateRadps;
        vx = linspace(max(-speed, previousCommand(1) - 0.20), ...
            min(speed, previousCommand(1) + 0.20), 5);
        vy = linspace(max(-speed, previousCommand(2) - 0.20), ...
            min(speed, previousCommand(2) + 0.20), 5);
        wz = linspace(max(-yawRate, previousCommand(3) - 0.35), ...
            min(yawRate, previousCommand(3) + 0.35), 5);
        candidates = zeros(3, numel(vx) * numel(vy) * numel(wz));
        index = 0;
        for ix = 1:numel(vx)
            for iy = 1:numel(vy)
                for iz = 1:numel(wz)
                    index = index + 1;
                    candidates(:, index) = [vx(ix); vy(iy); wz(iz)];
                end
            end
        end
        costs = zeros(1, size(candidates, 2));
        for index = 1:size(candidates, 2)
            rollout = localRollout(state, candidates(:, index), ...
                localCfg.timing.horizonSteps, localCfg);
            costs(index) = localRolloutCost(rollout, goal) + ...
                0.08 * norm(candidates(:, index) - previousCommand);
        end
        [~, selected] = min(costs);
        command = localSlew(candidates(:, selected), previousCommand, localCfg);
        label = "DWA_SUCCESS";
        end

        function [command, label] = localMppi(state, goal, previousCommand, localCfg)
        horizon = min(8, localCfg.timing.horizonSteps);
        samples = 64;
        nominal = localNominal(state, goal, horizon * localCfg.timing.sampleTimeS, localCfg);
        sequences = zeros(3, horizon, samples);
        costs = zeros(1, samples);
        noiseScale = [0.12; 0.12; 0.20];
        for sample = 1:samples
            last = previousCommand;
            for stage = 1:horizon
                candidate = nominal + noiseScale .* randn(3, 1);
                last = localSlew(candidate, last, localCfg);
                sequences(:, stage, sample) = last;
            end
            rollout = localRolloutSequence(state, sequences(:, :, sample), localCfg);
            costs(sample) = localRolloutCost(rollout, goal) + ...
                0.02 * sum(vecnorm(diff([previousCommand, sequences(:, :, sample)], 1, 2)));
        end
        temperature = max(0.25, std(costs));
        weights = exp(-(costs - min(costs)) / temperature);
        weights = weights / sum(weights);
        command = localSlew(squeeze(sum(sequences(:, 1, :) .* reshape(weights, 1, 1, []), 3)), ...
            previousCommand, localCfg);
        label = "MPPI_SUCCESS";
        end

        function [command, label] = localCca(state, goal, previousCommand, localCfg)
        nominal = localNominal(state, goal, localCfg.timing.sampleTimeS, localCfg);
        scales = [0.55, 0.75, 0.95, 1.10];
        [command, ~] = localBestConstant(state, goal, previousCommand, nominal, ...
            scales, localCfg);
        label = "CCA_NMPC_CONTEXT_NOT_SUPPLIED";
        end

        function [command, cost] = localBestConstant(state, goal, previousCommand, nominal, scales, localCfg)
        cost = inf;
        command = localSlew(nominal, previousCommand, localCfg);
        for scale = scales
            candidate = localSlew(scale * nominal, previousCommand, localCfg);
            rollout = localRollout(state, candidate, localCfg.timing.horizonSteps, localCfg);
            candidateCost = localRolloutCost(rollout, goal) + ...
                0.08 * norm(candidate - previousCommand);
            if candidateCost < cost
                cost = candidateCost;
                command = candidate;
            end
        end
        end

        function command = localNominal(state, goal, lookahead, localCfg)
        worldVelocity = (goal(1:2) - state(1:2)) / max(lookahead, localCfg.timing.sampleTimeS);
        speed = norm(worldVelocity);
        if speed > localCfg.position.maxSpeedMps
            worldVelocity = worldVelocity * localCfg.position.maxSpeedMps / speed;
        end
        psi = state(3);
        bodyVelocity = [cos(psi) * worldVelocity(1) + sin(psi) * worldVelocity(2); ...
            -sin(psi) * worldVelocity(1) + cos(psi) * worldVelocity(2)];
        yawError = atan2(sin(goal(3) - state(3)), cos(goal(3) - state(3)));
        command = [bodyVelocity; yawError / max(lookahead, localCfg.timing.sampleTimeS)];
        command(3) = min(localCfg.position.maxYawRateRadps, ...
            max(-localCfg.position.maxYawRateRadps, command(3)));
        end

        function command = localSlew(command, previousCommand, localCfg)
        limits = [localCfg.position.maxSpeedMps; localCfg.position.maxSpeedMps; ...
            localCfg.position.maxYawRateRadps];
        command = min(limits, max(-limits, command));
        deltaLimit = [0.20; 0.20; 0.35];
        delta = min(deltaLimit, max(-deltaLimit, command - previousCommand));
        command = previousCommand + delta;
        command = min(limits, max(-limits, command));
        end

        function rollout = localRollout(state, command, horizon, localCfg)
        rollout = zeros(6, horizon + 1);
        rollout(:, 1) = state;
        for stage = 1:horizon
            rollout(:, stage + 1) = cca.Model.positionStep( ...
                rollout(:, stage), command, localCfg.timing.sampleTimeS, ...
                localCfg.position.velocityTimeConstantS);
        end
        end

        function rollout = localRolloutSequence(state, sequence, localCfg)
        rollout = zeros(6, size(sequence, 2) + 1);
        rollout(:, 1) = state;
        for stage = 1:size(sequence, 2)
            rollout(:, stage + 1) = cca.Model.positionStep( ...
                rollout(:, stage), sequence(:, stage), localCfg.timing.sampleTimeS, ...
                localCfg.position.velocityTimeConstantS);
        end
        end

        function value = localRolloutCost(rollout, goal)
        positionError = rollout(1:2, :) - goal(1:2);
        yawError = atan2(sin(rollout(3, :) - goal(3)), ...
            cos(rollout(3, :) - goal(3)));
        value = sum(vecnorm(positionError, 2, 1).^2) + ...
            0.25 * sum(yawError.^2) + norm(positionError(:, end))^2;
        end
        end
    end
end
