classdef Nmpc
    methods (Static)
        function row = chanceRow(state, safety, epsilon, event, cfg)
        %CHANCEROW Frozen-half-space Gaussian row using direct relative covariance.
        
        normal = safety.separatingDirection(:, event);
        assert(abs(norm(normal) - 1) < 1e-10, ...
            "cca:control:SeparatingDirection", ...
            "Frozen separating directions must have unit norm.");
        projectedSeparation = normal' * ...
            (state(1:2) - safety.meanPositionM(:, event));
        worldVelocity = localWorldVelocity(state);
        closing = max(0, normal' * ...
            (safety.meanVelocityMps(:, event) - worldVelocity));
        relativeCovariance = safety.relativeCovarianceM2(:, :, event);
        assert(isequal(size(relativeCovariance), [2, 2]) && ...
            all(isfinite(relativeCovariance), "all"), ...
            "cca:control:RelativeCovariance", ...
            "Relative covariance must be finite and have shape 2-by-2.");
        scale = max(1, max(abs(relativeCovariance), [], "all"));
        assert(max(abs(relativeCovariance - relativeCovariance'), [], "all") ...
            <= 1e-9 * scale, ...
            "cca:control:RelativeCovarianceSymmetry", ...
            "Relative covariance must be symmetric.");
        relativeCovariance = 0.5 * ...
            (relativeCovariance + relativeCovariance');
        assert(min(eig(relativeCovariance)) >= -1e-9 * scale, ...
            "cca:control:RelativeCovariancePsd", ...
            "Relative covariance must be positive semidefinite.");
        variance = normal' * relativeCovariance * normal;
        quantile = sqrt(2) * erfcinv(2 * epsilon);
        brakingAcceleration = cca.Safety.brakingAcceleration(normal, state, cfg);
        braking = cfg.timing.commandDelayS * closing + ...
            closing^2 / (2 * brakingAcceleration);
        humanSupport = cca.Safety.ellipseSupport(normal, ...
            cfg.safety.humanEllipseSemiaxesM, localHumanYaw(safety, event));
        required = cfg.safety.robotRadiusM + humanSupport + ...
            cfg.safety.clearanceM + quantile * sqrt(max(variance, ...
            cfg.safety.chanceVarianceFloorM2)) + braking;
        row = required - projectedSeparation;
        function velocity = localWorldVelocity(state)
        psi = state(3);
        velocity = [cos(psi), -sin(psi); ...
                    sin(psi),  cos(psi)] * state(4:5);
        end
        
        function yaw = localHumanYaw(safety, index)
        if isfield(safety, "humanYawRad")
            yaw = safety.humanYawRad(index);
        else
            yaw = 0;
        end
        end
        
        end

        function [rows, gradients] = chanceRows( ...
            states, safety, strategy, cfg, relaxation)
        %CHANCEROWS Event rows and localized state Jacobians.
        
        if nargin < 5 || isempty(relaxation)
            relaxation = zeros(cfg.timing.horizonSteps, 1);
        end
        assert(isequal(size(relaxation), [cfg.timing.horizonSteps, 1]) && ...
            all(isfinite(relaxation) & relaxation >= 0));
        
        events = safety.events;
        eventCount = numel(events.probability);
        assert(all(size(safety.meanPositionM) == [2, eventCount]));
        assert(all(size(safety.meanVelocityMps) == [2, eventCount]));
        assert(all(size(safety.relativeCovarianceM2) == [2, 2, eventCount]));
        assert(all(size(safety.separatingDirection) == [2, eventCount]));
        allocation = cca.Risk.allocate(strategy, events, cfg);
        rows = zeros(eventCount, 1);
        gradients = zeros(numel(states), eventCount);
        
        for i = 1:eventCount
            stage = events.stageIndex(i);
            state = states(:, stage + 1);
            rows(i) = cca.Nmpc.chanceRow( ...
                state, safety, allocation.conditionalEpsilon(i), i, cfg) - ...
                relaxation(stage);
            if nargout > 1
                indices = (6 * stage + 1):(6 * (stage + 1));
                gradients(indices, i) = localGradient( ...
                    state, safety, allocation.conditionalEpsilon(i), i, cfg);
            end
        end
        function gradient = localGradient(state, safety, epsilon, event, cfg)
        gradient = zeros(6, 1);
        step = 1e-6 * max(1, abs(state));
        for j = 1:6
            delta = zeros(6, 1);
            delta(j) = step(j);
            plus = cca.Nmpc.chanceRow( ...
                state + delta, safety, epsilon, event, cfg);
            minus = cca.Nmpc.chanceRow( ...
                state - delta, safety, epsilon, event, cfg);
            gradient(j) = (plus - minus) / (2 * step(j));
        end
        end
        
        end

        function [matrix, bound] = linearConstraints(previousTorque, cfg)
        %LINEARCONSTRAINTS Torque-slew and wheel-speed inequalities.
        
        N = cfg.timing.horizonSteps;
        stateCount = 6 * (N + 1);
        variableCount = stateCount + 4 * N + ...
            N * double(cfg.risk.relaxationEnabled);
        matrix = zeros(16 * N, variableCount);
        bound = zeros(16 * N, 1);
        wheelMap = cca.Model.matrices(cfg.robot).wheelKinematics;
        wheelLimit = cfg.actuator.wheelSpeedMaxRadps;
        deltaMax = cfg.actuator.torqueRateMaxNmps * cfg.timing.sampleTimeS;
        
        for k = 1:N
            % Input u_k determines successor x_{k+1}; constrain x_1,...,x_N.
            xIndex = (6 * k + 1):(6 * (k + 1));
            uIndex = stateCount + (4 * (k - 1) + 1):(stateCount + 4 * k);
            rows = (16 * (k - 1) + 1):(16 * k);
            matrix(rows(1:4), uIndex) = eye(4);
            matrix(rows(5:8), uIndex) = -eye(4);
            if k == 1
                bound(rows(1:4)) = deltaMax + previousTorque;
                bound(rows(5:8)) = deltaMax - previousTorque;
            else
                previousIndex = uIndex - 4;
                matrix(rows(1:4), previousIndex) = -eye(4);
                matrix(rows(5:8), previousIndex) = eye(4);
                bound(rows(1:8)) = repmat(deltaMax, 2, 1);
            end
            matrix(rows(9:12), xIndex(4:6)) = wheelMap;
            matrix(rows(13:16), xIndex(4:6)) = -wheelMap;
            bound(rows(9:16)) = repmat(wheelLimit, 2, 1);
        end
        end

        function [inequality, equality, inequalityGradient, equalityGradient] = ...
            nmpcConstraints(decision, x0, reference, previousTorque, ...
            safety, strategy, cfg, appliedTorque)
        %NMPCCONSTRAINTS Multiple-shooting defects, terminal set and chance rows.
        
        if nargin < 8 || isempty(appliedTorque)
            appliedTorque = previousTorque;
        end
        N = cfg.timing.horizonSteps;
        [states, torques, relaxation] = ...
            cca.ControlPrimitives.unpackDecision(decision, N);
        actuation = cca.Controllers.actuatorPrediction( ...
            torques, previousTorque, appliedTorque, cfg);
        equality = zeros(6 * (N + 1), 1);
        equality(1:6) = states(:, 1) - x0;
        inequality = [];
        
        for k = 1:N
            prediction = cca.Model.rk4(states(:, k), ...
                actuation.effectiveTorques(:, k), zeros(3, 1), ...
                cfg.timing.sampleTimeS, cfg.robot);
            rows = (6 * k + 1):(6 * (k + 1));
            equality(rows) = states(:, k + 1) - prediction;
        end
        
        if cfg.terminal.enforce
            design = cca.Controllers.designLqr(cfg);
            terminal = localTerminalError(states(:, end), reference(:, end));
            terminalTorque = -design.K * terminal;
            switchDelta = terminalTorque - torques(:, end);
            deltaMax = cfg.actuator.torqueRateMaxNmps * ...
                cfg.timing.sampleTimeS;
            inequality = [ ...
                terminal' * design.P * terminal - cfg.terminal.rho; ...
                switchDelta - deltaMax; ...
               -switchDelta - deltaMax];
        end
        if isfield(safety, "active") && safety.active
            inequality = [inequality; ...
                cca.Nmpc.chanceRows( ...
                    states, safety, strategy, cfg, relaxation)];
        end
        
        if nargout > 2
            [inequalityGradient, equalityGradient] = localGradients( ...
                states, torques, reference, previousTorque, safety, ...
                strategy, cfg, appliedTorque, numel(inequality), relaxation);
        end
        function [GC, GCeq] = localGradients(states, torques, reference, ...
            previousTorque, safety, strategy, cfg, appliedTorque, count, relaxation)
        N = cfg.timing.horizonSteps;
        stateCount = 6 * (N + 1);
        baseVariableCount = stateCount + 4 * N;
        variableCount = baseVariableCount + ...
            N * double(cfg.risk.relaxationEnabled);
        actuation = cca.Controllers.actuatorPrediction( ...
            torques, previousTorque, appliedTorque, cfg);
        GCeq = zeros(variableCount, 6 * (N + 1));
        GCeq(1:6, 1:6) = eye(6);
        for k = 1:N
            xIndex = (6 * (k - 1) + 1):(6 * k);
            nextIndex = xIndex + 6;
            rows = (6 * k + 1):(6 * (k + 1));
            [A, B] = cca.Model.linearize( ...
                states(:, k), actuation.effectiveTorques(:, k), ...
                zeros(3, 1), cfg);
            GCeq(xIndex, rows) = -A';
            GCeq(nextIndex, rows) = eye(6);
            controlRows = (stateCount + 1):baseVariableCount;
            sensitivity = actuation.sensitivities(:, :, k);
            GCeq(controlRows, rows) = -(B * sensitivity)';
        end
        
        GC = zeros(variableCount, count);
        if cfg.terminal.enforce
            design = cca.Controllers.designLqr(cfg);
            terminal = localTerminalError(states(:, end), reference(:, end));
            finalIndex = (stateCount - 5):stateCount;
            GC(finalIndex, 1) = 2 * design.P * terminal;
            finalTorqueIndex = (baseVariableCount - 3):baseVariableCount;
            GC(finalIndex, 2:5) = -design.K';
            GC(finalTorqueIndex, 2:5) = -eye(4);
            GC(finalIndex, 6:9) = design.K';
            GC(finalTorqueIndex, 6:9) = eye(4);
        end
        if isfield(safety, "active") && safety.active
            [~, chanceGradient] = cca.Nmpc.chanceRows( ...
                states, safety, strategy, cfg, relaxation);
            offset = 9 * double(cfg.terminal.enforce);
            GC(1:stateCount, (offset + 1):end) = chanceGradient;
            if cfg.risk.relaxationEnabled
                for event = 1:numel(safety.events.stageIndex)
                    stage = safety.events.stageIndex(event);
                    GC(baseVariableCount + stage, offset + event) = -1;
                end
            end
        end
        end
        
        function error = localTerminalError(state, reference)
        error = state - reference;
        error(3) = atan2(sin(error(3)), cos(error(3)));
        end
        
        end

        function [value, gradient] = nmpcObjective( ...
            decision, reference, previousTorque, cfg)
        %NMPCOBJECTIVE Shared tracking, effort, slew and terminal objective.
        
        N = cfg.timing.horizonSteps;
        [states, torques, relaxation] = ...
            cca.ControlPrimitives.unpackDecision(decision, N);
        value = 0;
        stateGradient = zeros(size(states));
        torqueGradient = zeros(size(torques));
        last = previousTorque;
        wheelMap = cca.Model.matrices(cfg.robot).wheelKinematics;
        wheelProfile = cca.ControlPrimitives.nmpcWheelSpeedProfile(cfg);
        for k = 1:N
            error = states(:, k) - reference(:, k);
            error(3) = atan2(sin(error(3)), cos(error(3)));
            delta = torques(:, k) - last;
            value = value + error' * cfg.cost.Q * error + ...
                torques(:, k)' * cfg.cost.R * torques(:, k) + ...
                delta' * cfg.cost.RDelta * delta;
            stateGradient(:, k) = stateGradient(:, k) + 2 * cfg.cost.Q * error;
            torqueGradient(:, k) = torqueGradient(:, k) + ...
                2 * cfg.cost.R * torques(:, k) + ...
                2 * cfg.cost.RDelta * delta;
            if k > 1
                torqueGradient(:, k - 1) = torqueGradient(:, k - 1) - ...
                    2 * cfg.cost.RDelta * delta;
            end
            wheel = wheelMap * states(4:6, k + 1);
            excess = abs(wheel) - wheelProfile(:, k);
            active = excess > 0;
            if any(active)
                penalty = excess(active);
                weight = cfg.cost.wheelSpeedTighteningWeight;
                value = value + weight * (penalty' * penalty);
                wheelGradient = zeros(4, 1);
                wheelGradient(active) = ...
                    2 * weight * sign(wheel(active)) .* penalty;
                stateGradient(4:6, k + 1) = ...
                    stateGradient(4:6, k + 1) + wheelMap' * wheelGradient;
            end
            last = torques(:, k);
        end
        terminal = states(:, end) - reference(:, end);
        terminal(3) = atan2(sin(terminal(3)), cos(terminal(3)));
        value = value + terminal' * cfg.cost.QTerminal * terminal;
        stateGradient(:, end) = stateGradient(:, end) + ...
            2 * cfg.cost.QTerminal * terminal;
        hasRelaxation = numel(decision) > 6 * (N + 1) + 4 * N;
        if hasRelaxation
            value = value + cfg.risk.relaxationWeight * ...
                (relaxation' * relaxation);
            relaxationGradient = 2 * cfg.risk.relaxationWeight * relaxation;
            gradient = cca.ControlPrimitives.packDecision( ...
                stateGradient, torqueGradient, relaxationGradient);
        else
            gradient = cca.ControlPrimitives.packDecision(stateGradient, torqueGradient);
        end
        end

        function states = predictionRollout( ...
            initialState, commands, previousCommand, appliedTorque, cfg)
        %PREDICTIONROLLOUT Six-state rollout with actuator-history prediction.
        
        N = size(commands, 2);
        states = zeros(6, N + 1);
        states(:, 1) = initialState;
        actuation = cca.Controllers.actuatorPrediction( ...
            commands, previousCommand, appliedTorque, cfg);
        for k = 1:N
            states(:, k + 1) = cca.Model.rk4( ...
                states(:, k), actuation.effectiveTorques(:, k), ...
                zeros(3, 1), cfg.timing.sampleTimeS, cfg.robot);
        end
        end

        function solution = solveNmpc(x0, reference, previousTorque, safety, ...
            strategy, cfg, warmStart, appliedTorque)
        %SOLVENMPC Direct multiple-shooting nonlinear MPC solved by fmincon SQP.
        
        arguments
            x0 (6, 1) double {mustBeFinite}
            reference (6, :) double {mustBeFinite}
            previousTorque (4, 1) double {mustBeFinite}
            safety struct
            strategy (1, 1) string
            cfg struct
            warmStart double = []
            appliedTorque double = []
        end
        if isempty(appliedTorque)
            appliedTorque = previousTorque;
        end
        assert(isequal(size(appliedTorque), [4, 1]) && all(isfinite(appliedTorque)));
        
        N = cfg.timing.horizonSteps;
        assert(size(reference, 2) == N + 1);
        nx = 6;
        nu = 4;
        if isempty(warmStart)
            U0 = repmat(previousTorque, 1, N);
            X0 = cca.Nmpc.predictionRollout( ...
                x0, U0, previousTorque, appliedTorque, cfg);
            if cfg.risk.relaxationEnabled
                z0 = cca.ControlPrimitives.packDecision(X0, U0, zeros(N, 1));
            else
                z0 = cca.ControlPrimitives.packDecision(X0, U0);
            end
        else
            z0 = warmStart(:);
            expected = nx * (N + 1) + nu * N + ...
                N * double(cfg.risk.relaxationEnabled);
            assert(numel(z0) == expected);
        end
        
        lower = [-inf(nx * (N + 1), 1); ...
            repmat(cfg.actuator.torqueMinNm, N, 1); ...
            zeros(N * double(cfg.risk.relaxationEnabled), 1)];
        upper = [inf(nx * (N + 1), 1); ...
            repmat(cfg.actuator.torqueMaxNm, N, 1); ...
            inf(N * double(cfg.risk.relaxationEnabled), 1)];
        options = optimoptions("fmincon", ...
            Algorithm=cfg.solver.algorithm, ...
            Display=cfg.solver.display, ...
            MaxIterations=cfg.solver.maxIterations, ...
            MaxFunctionEvaluations=cfg.solver.maxFunctionEvaluations, ...
            ConstraintTolerance=cfg.solver.constraintTolerance, ...
            OptimalityTolerance=cfg.solver.optimalityTolerance, ...
            StepTolerance=cfg.solver.stepTolerance, ...
            SpecifyObjectiveGradient=true, ...
            SpecifyConstraintGradient=true);
        [linearMatrix, linearBound] = cca.Nmpc.linearConstraints( ...
            previousTorque, cfg);
        
        timer = tic;
        [z, objective, exitflag, output] = fmincon( ...
            @(decision) cca.Nmpc.nmpcObjective( ...
                decision, reference, previousTorque, cfg), ...
            z0, linearMatrix, linearBound, [], [], lower, upper, ...
            @(decision) cca.Nmpc.nmpcConstraints( ...
                decision, x0, reference, previousTorque, ...
                safety, strategy, cfg, appliedTorque), options);
        elapsed = toc(timer);
        [X, U, relaxation] = cca.ControlPrimitives.unpackDecision(z, N);
        finiteDecision = all(isfinite(z));
        if finiteDecision
            [nonlinearInequality, nonlinearEquality] = ...
                cca.Nmpc.nmpcConstraints(z, x0, reference, previousTorque, ...
                safety, strategy, cfg, appliedTorque);
            constraintViolation = max([0; linearMatrix * z - linearBound; ...
                lower - z; z - upper; nonlinearInequality; ...
                abs(nonlinearEquality)]);
        else
            constraintViolation = inf;
        end
        
        solution.states = X;
        solution.torques = U;
        solution.firstTorque = U(:, 1);
        solution.objective = objective;
        solution.exitflag = exitflag;
        solution.output = output;
        solution.solveTimeS = elapsed;
        solution.maxConstraintViolation = constraintViolation;
        solution.success = exitflag > 0 && finiteDecision && ...
            constraintViolation <= cfg.solver.constraintTolerance;
        solution.maximumChanceRelaxationM = max(relaxation, [], "all");
        calibrationHashValid = false;
        if isfield(cfg, "context") && ...
                isfield(cfg.context, "calibrationHash")
            calibrationHash = char(string(cfg.context.calibrationHash));
            calibrationHashValid = ~isempty(regexp( ...
                calibrationHash, "^[0-9A-Fa-f]{64}$", "once"));
        end
        calibrationDomainValid = isfield(cfg, "context") && ...
            isfield(cfg.context, "calibrationDomain") && ...
            strlength(string(cfg.context.calibrationDomain)) > 0;
        evidenceComplete = isfield(cfg, "context") && ...
            isfield(cfg.context, "calibrationValid") && ...
            cfg.context.calibrationValid && calibrationHashValid && ...
            calibrationDomainValid && ...
            isfield(cfg.context, "calibrationTailVerified") && ...
            cfg.context.calibrationTailVerified && ...
            isfield(cfg.context, "frameTimeAgeVerified") && ...
            cfg.context.frameTimeAgeVerified && ...
            isfield(cfg.context, "modePartitionVerified") && ...
            cfg.context.modePartitionVerified && ...
            isfield(cfg.context, "covarianceProvenanceVerified") && ...
            cfg.context.covarianceProvenanceVerified && ...
            isfield(cfg.context, "geometryContainmentVerified") && ...
            cfg.context.geometryContainmentVerified;
        solution.probabilityClaimEligible = solution.success && ...
            isfield(safety, "active") && safety.active && ...
            solution.maximumChanceRelaxationM <= ...
            cfg.risk.probabilityZeroToleranceM && evidenceComplete;
        if cfg.risk.relaxationEnabled
            solution.warmStart = cca.ControlPrimitives.shiftWarmStart(X, U, relaxation);
        else
            solution.warmStart = cca.ControlPrimitives.shiftWarmStart(X, U);
        end
        end
    end
end
