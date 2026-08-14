classdef AnalysisTools
    methods (Static)
        function study = feedbackNecessity(cfg)
            target = [1; 1; 0; 0; 0; 0];
            nominal = cfg;
            nominal.study.plantMode = "nominal";
            nominal.study.constantDisturbance = zeros(3, 1);
            source = cca.Simulation.simulate("LQR", target, nominal);
            mismatch = cfg;
            mismatch.study.plantMode = "mismatched";
            mismatch.study.constantDisturbance = [0.5; -0.3; 0.05];
            replay = cca.AnalysisTools.localReplay(source.torques, target, mismatch);
            feedback = cca.Simulation.simulate("LQR", target, mismatch);
            study.summary = [ ...
                cca.AnalysisTools.localRow("NOMINAL_CLOSED_LOOP_SOURCE", ...
                source, target, nominal); ...
                cca.AnalysisTools.localRow("MISMATCH_OPEN_LOOP_REPLAY", ...
                replay, target, mismatch); ...
                cca.AnalysisTools.localRow("MISMATCH_CLOSED_LOOP_FEEDBACK", ...
                feedback, target, mismatch)];
            study.source = source;
            study.replay = replay;
            study.feedback = feedback;
        end

        function report = localNmpcStability(cfg)
            local = cfg;
            local.timing.horizonSteps = 3;
            local.terminal.enforce = true;
            sampleCount = 12;
            design = cca.Controllers.designLqr(local);
            directions = cca.AnalysisTools.localDirections(sampleCount);
            points = 0.5 * sqrt(local.terminal.rho) * ...
                (chol(design.P) \ directions);
            safety.active = false;
            firstSuccess = false(sampleCount, 1);
            recursiveSuccess = false(sampleCount, 1);
            constraintResidual = inf(sampleCount, 1);
            valueChange = inf(sampleCount, 1);
            for i = 1:sampleCount
                state = points(:, i);
                previous = -design.K * state;
                reference = zeros(6, local.timing.horizonSteps + 1);
                first = cca.Nmpc.solveNmpc(state, reference, previous, ...
                    safety, "NONE", local);
                firstSuccess(i) = first.success;
                if ~first.success
                    continue;
                end
                decision = cca.ControlPrimitives.packDecision( ...
                    first.states, first.torques);
                [ci, ceq] = cca.Nmpc.nmpcConstraints( ...
                    decision, state, reference, previous, safety, "NONE", local);
                constraintResidual(i) = max([ci; abs(ceq)]);
                next = cca.Model.rk4(state, first.firstTorque, zeros(3, 1), ...
                    local.timing.sampleTimeS, local.robot);
                second = cca.Nmpc.solveNmpc(next, reference, ...
                    first.firstTorque, safety, "NONE", local, first.warmStart);
                recursiveSuccess(i) = second.success;
                if second.success
                    valueChange(i) = second.objective - first.objective;
                end
            end
            report.InitialCases = sampleCount;
            report.FirstSolveSuccessRate = mean(firstSuccess);
            report.RecursiveSolveSuccessRate = mean(recursiveSuccess);
            report.MaximumConstraintResidual = max(constraintResidual);
            report.MaximumOptimalValueChange = max(valueChange);
            report.Pass = all(firstSuccess) && all(recursiveSuccess) && ...
                report.MaximumConstraintResidual <= local.solver.constraintTolerance;
            report.Scope = ...
                "sampled local two-step feasibility; no Lyapunov-decrease claim";
        end

        function report = modelDiscrepancy(cfg)
            steps = round(2 / cfg.timing.sampleTimeS);
            requestedWrench = cfg.study.openLoopStepWrench;
            torque = cca.ControlPrimitives.minimumNormTorque( ...
                requestedWrench, cfg);
            torque = min(cfg.actuator.torqueMaxNm, ...
                max(cfg.actuator.torqueMinNm, torque));
            commands = repmat(torque, 1, steps);
            model = cca.Model.rollout(zeros(6, 1), commands, zeros(3, 1), ...
                cfg.timing.sampleTimeS, cfg.robot);
            plant = cca.Plant.rollout( ...
                zeros(6, 1), commands, zeros(3, 1), cfg);
            error = model - plant(1:6, :);
            report.oneStepStateError = norm(error(:, 2));
            report.horizonStateError = norm(error(:, end));
            report.maximumPositionErrorM = max(vecnorm(error(1:2, :)));
            report.maximumVelocityError = max(vecnorm(error(4:6, :)));
            report.modelStates = model;
            report.plantStates = plant;
        end

        function report = numericalParity(cfg)
            x0 = [0.1; -0.1; 0.2; 0.3; -0.1; 0.15];
            torque = [0.2; -0.1; 0.15; 0.05];
            disturbance = [0.1; -0.05; 0.02];
            steps = round(2 / cfg.timing.sampleTimeS);
            commands = repmat(torque, 1, steps);
            coarse = cca.Model.rollout(x0, commands, disturbance, ...
                cfg.timing.sampleTimeS, cfg.robot);
            fine = cca.AnalysisTools.localFineRollout(x0, commands, disturbance, cfg);
            error = coarse - fine;
            report.oneStepStateError = norm(error(:, 2));
            report.horizonStateError = norm(error(:, end));
            report.maximumPositionErrorM = max(vecnorm(error(1:2, :)));
            report.maximumYawErrorRad = max(abs(error(3, :)));
            report.maximumVelocityError = max(vecnorm(error(4:6, :)));
            report.fineSubsteps = cfg.study.numericalParitySubsteps;
            limit = cfg.study.numericalParityTolerance;
            report.pass = ...
                report.oneStepStateError <= limit.oneStepStateError && ...
                report.horizonStateError <= limit.horizonStateError && ...
                report.maximumPositionErrorM <= limit.maximumPositionErrorM && ...
                report.maximumYawErrorRad <= limit.maximumYawErrorRad && ...
                report.maximumVelocityError <= limit.maximumVelocityError;
        end

        function report = openLoop(cfg)
            model = cca.Model.matrices(cfg.robot);
            [A, B] = cca.Model.linearize(zeros(6, 1), zeros(4, 1), ...
                zeros(3, 1), cfg);
            [Ac, Bc] = cca.Model.linearizeContinuous( ...
                zeros(6, 1), zeros(4, 1), zeros(3, 1), cfg.robot);
            augmented = expm([Ac, Bc; zeros(4, 10)] * cfg.timing.sampleTimeS);
            AdExact = augmented(1:6, 1:6);
            BdExact = augmented(1:6, 7:10);
            report.effectiveInertiaEigenvalues = eig(model.effectiveInertia);
            report.continuousPoles = eig(Ac);
            report.discretePoles = eig(A);
            report.continuousControllabilityRank = ...
                cca.AnalysisTools.localRank(Ac, Bc);
            report.controllabilityRank = cca.AnalysisTools.localRank(A, B);
            report.zohStateMatrixError = norm(A - AdExact, 2);
            report.zohInputMatrixError = norm(B - BdExact, 2);
            report.zohParityPass = ...
                max(report.zohStateMatrixError, report.zohInputMatrixError) <= ...
                cfg.study.zohParityTolerance;
            report.inputRank = model.inputRank;
            report.inputNullity = size(model.inputNullspace, 2);
            report.nullspaceResidual = norm(model.bodyWrenchMap * model.inputNullspace);
            report.equilibriumResidual = norm(cca.Model.dynamics( ...
                zeros(6, 1), zeros(4, 1), zeros(3, 1), cfg.robot));
            torque = [0.2; -0.1; 0.15; 0.05];
            twist = [0.3; -0.2; 0.1];
            report.powerDualityResidual = abs( ...
                torque' * model.wheelKinematics * twist - ...
                (model.bodyWrenchMap * torque)' * twist);
            report.minimumInputSingularValue = min(svd(model.bodyWrenchMap));
            report.A = A;
            report.B = B;
            report.Ac = Ac;
            report.Bc = Bc;
        end

        function rows = openLoopChannels(cfg)
            names = ["forward"; "lateral"; "yaw"];
            wrenches = cfg.study.openLoopChannelWrenches;
            steps = round(2 / cfg.timing.sampleTimeS);
            rows = cell(3, 1);
            for i = 1:3
                requested = wrenches(:, i);
                torque = cca.ControlPrimitives.minimumNormTorque( ...
                    requested, cfg);
                torque = min(cfg.actuator.torqueMaxNm, ...
                    max(cfg.actuator.torqueMinNm, torque));
                achieved = cca.Model.matrices(cfg.robot).bodyWrenchMap * torque;
                commands = repmat(torque, 1, steps);
                nominal = cca.Model.rollout(zeros(6, 1), commands, zeros(3, 1), ...
                    cfg.timing.sampleTimeS, cfg.robot);
                mismatched = cca.Plant.rollout( ...
                    zeros(6, 1), commands, zeros(3, 1), cfg);
                axis = zeros(3, 1);
                axis(i) = 1;
                crossProjector = eye(3) - axis * axis';
                rows{i} = table(names(i), norm(achieved - requested), ...
                    axis' * nominal(4:6, end), ...
                    axis' * mismatched(4:6, end), ...
                    norm(crossProjector * nominal(4:6, end)), ...
                    norm(nominal(:, end) - mismatched(1:6, end)), ...
                    VariableNames=["Channel", "WrenchAllocationResidual", ...
                    "NominalFinalRate", "MismatchedFinalRate", ...
                    "NominalCrossAxisRate", "FinalStateDiscrepancy"]);
            end
            rows = vertcat(rows{:});
        end

        function rows = openLoopPulseChannels(cfg)
            names = ["forward"; "lateral"; "yaw"];
            wrenches = cfg.study.openLoopChannelWrenches;
            steps = round(2 / cfg.timing.sampleTimeS);
            rows = cell(3, 1);
            for i = 1:3
                requested = wrenches(:, i);
                torque = cca.ControlPrimitives.minimumNormTorque( ...
                    requested, cfg);
                torque = cca.ControlPrimitives.limitTorque( ...
                    torque, zeros(4, 1), cfg);
                commands = zeros(4, steps);
                commands(:, 1) = torque;
                nominal = cca.Model.rollout(zeros(6, 1), commands, zeros(3, 1), ...
                    cfg.timing.sampleTimeS, cfg.robot);
                mismatched = cca.Plant.rollout( ...
                    zeros(6, 1), commands, zeros(3, 1), cfg);
                axis = zeros(3, 1);
                axis(i) = 1;
                nominalRate = axis' * nominal(4:6, :);
                mismatchedRate = axis' * mismatched(4:6, :);
                crossProjector = eye(3) - axis * axis';
                achieved = cca.Model.matrices(cfg.robot).bodyWrenchMap * torque;
                rows{i} = table(names(i), norm(achieved - requested), ...
                    max(nominalRate), nominalRate(end), ...
                    max(mismatchedRate), mismatchedRate(end), ...
                    max(vecnorm(crossProjector * nominal(4:6, :))), ...
                    max(vecnorm(nominal - mismatched(1:6, :))), ...
                    VariableNames=["Channel", "WrenchAllocationResidual", ...
                    "NominalPeakRate", "NominalFinalRate", ...
                    "MismatchedPeakRate", "MismatchedFinalRate", ...
                    "NominalCrossAxisPeakRate", "MaximumStateDiscrepancy"]);
            end
            rows = vertcat(rows{:});
        end

        function report = overActuation(cfg)
            model = cca.Model.matrices(cfg.robot);
            wrench = [10; -5; 1];
            minimum = cca.ControlPrimitives.minimumNormTorque(wrench, cfg);
            nullVector = model.inputNullspace(:, 1);
            gainLimit = cca.AnalysisTools.localPositiveGainLimit( ...
                minimum, nullVector, cfg.actuator.torqueMinNm, ...
                cfg.actuator.torqueMaxNm);
            nullGain = 0.5 * gainLimit;
            alternative = minimum + nullGain * nullVector;
            steps = round(1 / cfg.timing.sampleTimeS);
            minimumStates = cca.Model.rollout(zeros(6, 1), ...
                repmat(minimum, 1, steps), zeros(3, 1), ...
                cfg.timing.sampleTimeS, cfg.robot);
            alternativeStates = cca.Model.rollout(zeros(6, 1), ...
                repmat(alternative, 1, steps), zeros(3, 1), ...
                cfg.timing.sampleTimeS, cfg.robot);
            report = table( ...
                norm(model.bodyWrenchMap * minimum - wrench), ...
                norm(model.bodyWrenchMap * alternative - wrench), ...
                norm(minimum)^2, norm(alternative)^2, ...
                abs(nullVector' * minimum), abs(nullVector' * alternative), ...
                min(cfg.actuator.torqueMaxNm - abs(minimum)), ...
                min(cfg.actuator.torqueMaxNm - abs(alternative)), ...
                max(abs(minimumStates - alternativeStates), [], "all"), ...
                VariableNames=["MinimumWrenchResidual", ...
                "NullShiftedWrenchResidual", "MinimumSquaredEffort", ...
                "NullShiftedSquaredEffort", "MinimumNullComponent", ...
                "NullShiftedNullComponent", "MinimumTorqueHeadroomNm", ...
                "NullShiftedTorqueHeadroomNm", "MaximumStateDifference"]);
        end

        function report = regionOfAttraction(cfg)
            n = cfg.study.roaGridPointsPerAxis;
            positions = linspace(-cfg.study.roaPositionRangeM, ...
                cfg.study.roaPositionRangeM, n);
            yaws = linspace(-cfg.study.roaYawRangeRad, ...
                cfg.study.roaYawRangeRad, n);
            design = cca.Controllers.designLqr(cfg);
            steps = round(cfg.study.durationS / cfg.timing.sampleTimeS);
            count = n ^ 3;
            converged = false(count, 1);
            wheelViolation = false(count, 1);
            finalPoseError = zeros(count, 1);
            finalVelocityError = zeros(count, 1);
            index = 0;
            model = cca.Model.matrices(cfg.robot);
            for px = positions
                for py = positions
                    for yaw = yaws
                        index = index + 1;
                        state = [px; py; yaw; 0; 0; 0];
                        previous = zeros(4, 1);
                        for k = 1:steps
                            errorState = state;
                            errorState(3) = atan2(sin(state(3)), cos(state(3)));
                            torque = cca.ControlPrimitives.limitTorque( ...
                                -design.K * errorState, previous, cfg);
                            state = cca.Model.rk4(state, torque, zeros(3, 1), ...
                                cfg.timing.sampleTimeS, cfg.robot);
                            wheel = model.wheelKinematics * state(4:6);
                            wheelViolation(index) = wheelViolation(index) || ...
                                any(abs(wheel) > cfg.actuator.wheelSpeedMaxRadps);
                            previous = torque;
                        end
                        finalPoseError(index) = norm(state(1:3));
                        finalVelocityError(index) = norm(state(4:6));
                        converged(index) = ...
                            finalPoseError(index) <= ...
                            cfg.study.roaFinalPoseTolerance && ...
                            finalVelocityError(index) <= ...
                            cfg.study.roaFinalVelocityTolerance && ...
                            ~wheelViolation(index);
                    end
                end
            end
            report.GridCases = count;
            report.ConvergedCases = nnz(converged);
            report.ConvergenceRate = mean(converged);
            report.WheelSpeedViolationCases = nnz(wheelViolation);
            report.WorstFinalPoseError = max(finalPoseError);
            report.WorstFinalVelocityError = max(finalVelocityError);
            report.Scope = "nominal LQR empirical pose/yaw grid; zero initial velocity";
        end

        function metrics = responseMetrics(time, signal, target, bandFraction)
            time = time(:);
            signal = signal(:);
            assert(numel(time) == numel(signal));
            initial = signal(1);
            amplitude = target - initial;
            error = target - signal;
            if abs(amplitude) < eps
                riseTime = NaN;
                overshoot = NaN;
                undershoot = NaN;
            else
                normalized = (signal - initial) / amplitude;
                i10 = find(normalized >= 0.1, 1, "first");
                i90 = find(normalized >= 0.9, 1, "first");
                riseTime = cca.AnalysisTools.localTimeDifference(time, i10, i90);
                overshoot = max(0, 100 * (max(normalized) - 1));
                undershoot = max(0, -100 * min(normalized));
            end
            band = max(abs(amplitude) * bandFraction, 1e-6);
            outside = find(abs(error) > band, 1, "last");
            if isempty(outside)
                settlingTime = 0;
            elseif outside == numel(time)
                settlingTime = NaN;
            else
                settlingTime = time(outside + 1);
            end
            metrics.riseTimeS = riseTime;
            metrics.settlingTimeS = settlingTime;
            metrics.overshootPercent = overshoot;
            metrics.undershootPercent = undershoot;
            metrics.responseMinimum = min(signal);
            metrics.responseMaximum = max(signal);
            metrics.maximumAbsoluteError = max(abs(error));
            metrics.steadyStateError = mean(error(max(1, end - 4):end));
            metrics.IAE = trapz(time, abs(error));
            metrics.ISE = trapz(time, error .^ 2);
            metrics.ITAE = trapz(time, time .* abs(error));
        end

        function result = scenarioOutcome(result, scenario, cfg)
            sampleCount = numel(result.timeS);
            contextCount = size(result.contextPositionM, 2);
            margin = inf(contextCount, sampleCount);
            humanYaw = cca.AnalysisTools.localHumanYaw(scenario, contextCount);
            for k = 1:sampleCount
                for human = 1:contextCount
                    difference = result.contextPositionM(:, human) - ...
                        result.states(1:2, k);
                    [normal, distance] = cca.AnalysisTools.localNormal(difference, cfg);
                    support = cfg.safety.robotRadiusM + ...
                        cca.Safety.ellipseSupport(normal, ...
                        cfg.safety.humanEllipseSemiaxesM, humanYaw(human));
                    margin(human, k) = distance - support;
                end
            end
            result.minimumPhysicalMarginM = min(margin, [], "all");
            result.collision = any(margin <= 0, "all");
            result.unsafeIntrusion = any( ...
                margin <= cfg.safety.clearanceM, "all");
            positionError = vecnorm( ...
                result.states(1:2, :) - result.target(1:2));
            yawError = abs(atan2( ...
                sin(result.states(3, :) - result.target(3)), ...
                cos(result.states(3, :) - result.target(3))));
            velocityError = vecnorm( ...
                result.states(4:6, :) - result.target(4:6));
            eligible = positionError <= cfg.study.goalToleranceM & ...
                yawError <= cfg.study.goalYawToleranceRad & ...
                velocityError <= cfg.study.goalVelocityTolerance;
            dwellSamples = ceil(cfg.study.goalDwellS / ...
                cfg.timing.sampleTimeS) + 1;
            first = cca.AnalysisTools.localFirstDwell(eligible, dwellSamples);
            result.completion = ~isempty(first);
            if result.completion
                result.goalTimeS = result.timeS(first + dwellSamples - 1);
            else
                result.goalTimeS = NaN;
            end
            result.goalEligible = eligible;
            result.physicalMarginM = margin;
        end

        function certificate = stability(cfg)
            design = cca.Controllers.designLqr(cfg);
            sample = cca.AnalysisTools.terminalDecrease( ...
                design, cfg, cfg.terminal.rho, cfg.terminal.sampleCount);
            slew = cca.AnalysisTools.terminalSlewMargins( ...
                design, cfg, cfg.terminal.rho, cfg.terminal.sampleCount);
            certificate.maxPoleMagnitude = max(abs(design.poles));
            certificate.minimumPEigenvalue = min(eig(design.P));
            certificate.dareResidualNorm = norm(design.dareResidual, 2);
            certificate.maximumTerminalResidualEigenvalue = ...
                max(eig(design.terminalResidual));
            certificate.terminalRho = cfg.terminal.rho;
            certificate.maximumSampledIncrease = max(sample);
            certificate.maximumTerminalSlewMarginNm = max(slew);
            certificate.pass = certificate.maxPoleMagnitude < 1 && ...
                certificate.minimumPEigenvalue > 0 && ...
                certificate.dareResidualNorm < 1e-7 && ...
                certificate.maximumTerminalResidualEigenvalue < 0 && ...
                certificate.maximumSampledIncrease <= ...
                cfg.terminal.decreaseTolerance && ...
                certificate.maximumTerminalSlewMarginNm <= 0;
            certificate.scope = ...
                "nominal local human-free terminal controller and sampled nonlinear set";
        end

        function values = terminalDecrease(design, cfg, rho, sampleCount)
            rngState = rng;
            cleanup = onCleanup(@() rng(rngState)); %#ok<NASGU>
            rng(27072026, "twister");
            directions = randn(6, sampleCount);
            directions = directions ./ vecnorm(directions);
            points = chol(design.P) \ directions;
            radii = rand(1, sampleCount) .^ (1 / 6);
            points = sqrt(rho) * points .* radii;
            values = zeros(1, sampleCount);
            for i = 1:sampleCount
                state = points(:, i);
                torque = -design.K * state;
                next = cca.Model.rk4(state, torque, zeros(3, 1), ...
                    cfg.timing.sampleTimeS, cfg.robot);
                stage = state' * cfg.cost.Q * state + ...
                    torque' * cfg.cost.R * torque;
                values(i) = next' * design.P * next - ...
                    state' * design.P * state + stage;
            end
        end

        function margins = terminalSlewMargins(design, cfg, rho, sampleCount)
            rngState = rng;
            cleanup = onCleanup(@() rng(rngState)); %#ok<NASGU>
            rng(27072026, "twister");
            directions = randn(6, sampleCount);
            directions = directions ./ vecnorm(directions);
            points = chol(design.P) \ directions;
            radii = rand(1, sampleCount) .^ (1 / 6);
            points = sqrt(rho) * points .* radii;
            deltaMax = cfg.actuator.torqueRateMaxNmps * ...
                cfg.timing.sampleTimeS;
            margins = zeros(1, sampleCount);
            for i = 1:sampleCount
                state = points(:, i);
                torque = -design.K * state;
                next = cca.Model.rk4(state, torque, zeros(3, 1), ...
                    cfg.timing.sampleTimeS, cfg.robot);
                nextTorque = -design.K * next;
                margins(i) = max(abs(nextTorque - torque) - deltaMax);
            end
        end
    end

    methods (Static, Access=private)
        function result = localReplay(commands, target, cfg)
            steps = size(commands, 2);
            states = zeros(6, steps + 1);
            previous = zeros(4, 1);
            plantState = [];
            for k = 1:steps
                command = commands(:, k);
                [states(:, k + 1), plantState] = cca.Plant.advance( ...
                    states(:, k), command, previous, plantState, cfg);
                previous = command;
            end
            result.states = states;
            result.torques = commands;
            result.timeS = (0:steps) * cfg.timing.sampleTimeS;
            result.target = target;
        end

        function row = localRow(mode, result, target, cfg)
            projection = [1; 1; 0] / sqrt(2);
            signal = projection' * result.states(1:3, :);
            targetValue = projection' * target(1:3);
            error = targetValue - signal;
            wheel = cca.Model.matrices(cfg.robot).wheelKinematics * ...
                result.states(4:6, 2:end);
            wheelExcess = abs(wheel) - cfg.actuator.wheelSpeedMaxRadps;
            row = table(mode, abs(error(end)), trapz(result.timeS, abs(error)), ...
                sqrt(mean(vecnorm(result.torques) .^ 2)), ...
                mean(any(wheelExcess > cfg.solver.constraintTolerance, 1)), ...
                max([0; wheelExcess(:)]), ...
                VariableNames=["Mode", "FinalProjectedError", "ProjectedIAE", ...
                "TorqueRmsNm", "WheelViolationRate", ...
                "WheelSpeedExcessPeakRadps"]);
        end

        function directions = localDirections(count)
            rngState = rng;
            cleanup = onCleanup(@() rng(rngState)); %#ok<NASGU>
            rng(27072026, "twister");
            directions = randn(6, count);
            directions = directions ./ vecnorm(directions);
        end

        function states = localFineRollout(x0, commands, disturbance, cfg)
            count = size(commands, 2);
            states = zeros(6, count + 1);
            states(:, 1) = x0;
            substeps = cfg.study.numericalParitySubsteps;
            dt = cfg.timing.sampleTimeS / substeps;
            for k = 1:count
                state = states(:, k);
                for j = 1:substeps
                    state = cca.Model.rk4( ...
                        state, commands(:, k), disturbance, dt, cfg.robot);
                end
                states(:, k + 1) = state;
            end
        end

        function value = localRank(A, B)
            matrix = B;
            block = B;
            for k = 1:(size(A, 1) - 1)
                block = A * block;
                matrix = [matrix, block]; %#ok<AGROW>
            end
            value = rank(matrix);
        end

        function limit = localPositiveGainLimit(torque, direction, lower, upper)
            limits = inf(size(direction));
            positive = direction > 0;
            negative = direction < 0;
            limits(positive) = (upper(positive) - torque(positive)) ./ ...
                direction(positive);
            limits(negative) = (lower(negative) - torque(negative)) ./ ...
                direction(negative);
            limit = min(limits);
            assert(isfinite(limit) && limit > 0);
        end

        function value = localTimeDifference(time, firstIndex, secondIndex)
            if isempty(firstIndex) || isempty(secondIndex)
                value = NaN;
            else
                value = time(secondIndex) - time(firstIndex);
            end
        end

        function yaw = localHumanYaw(scenario, count)
            if isfield(scenario, "humanYawRad")
                yaw = scenario.humanYawRad(:);
                assert(numel(yaw) == count);
            else
                yaw = zeros(count, 1);
            end
        end

        function [normal, distance] = localNormal(difference, cfg)
            distance = norm(difference);
            if distance < cfg.safety.minimumNormalDistanceM
                normal = [1; 0];
            else
                normal = difference / distance;
            end
        end

        function first = localFirstDwell(eligible, count)
            if numel(eligible) < count
                first = [];
                return;
            end
            windows = conv(double(eligible), ones(1, count), "valid");
            first = find(windows == count, 1, "first");
        end
    end
end
