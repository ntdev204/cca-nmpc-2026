classdef Controllers
    methods (Static)
        function prediction = actuatorPrediction( ...
            commands, previousCommand, appliedTorque, cfg)
        %ACTUATORPREDICTION One-delay-sample first-order torque prediction.
        
        N = size(commands, 2);
        variableCount = 4 * N;
        beta = exp(-cfg.timing.sampleTimeS / ...
            cfg.controller.actuatorPredictionTimeConstantS);
        current = appliedTorque;
        currentSensitivity = zeros(4, variableCount);
        prediction.effectiveTorques = zeros(4, N);
        prediction.sensitivities = zeros(4, variableCount, N);
        
        for k = 1:N
            delayedSensitivity = zeros(4, variableCount);
            if k == 1
                delayed = previousCommand;
            else
                delayed = commands(:, k - 1);
                columns = (4 * (k - 2) + 1):(4 * (k - 1));
                delayedSensitivity(:, columns) = eye(4);
            end
            next = beta * current + (1 - beta) * delayed;
            nextSensitivity = beta * currentSensitivity + ...
                (1 - beta) * delayedSensitivity;
            prediction.effectiveTorques(:, k) = 0.5 * (current + next);
            prediction.sensitivities(:, :, k) = ...
                0.5 * (currentSensitivity + nextSensitivity);
            current = next;
            currentSensitivity = nextSensitivity;
        end
        prediction.finalAppliedTorque = current;
        end

        function torque = bodyPidTorque(state, target, integralPoseError, cfg)
        %BODYPIDTORQUE Cascaded pose/body-velocity baseline with torque allocation.
        
        poseErrorWorld = target(1:3) - state(1:3);
        poseErrorWorld(3) = atan2(sin(poseErrorWorld(3)), ...
            cos(poseErrorWorld(3)));
        psi = state(3);
        worldToBody = [cos(psi), sin(psi), 0; ...
                      -sin(psi), cos(psi), 0; ...
                       0,        0,       1];
        poseErrorBody = worldToBody * poseErrorWorld;
        integralBody = worldToBody * integralPoseError;
        
        desiredVelocity = cfg.pid.poseKp .* poseErrorBody + ...
            cfg.pid.poseKi .* integralBody;
        desiredVelocity = min(cfg.pid.velocityMax, ...
            max(-cfg.pid.velocityMax, desiredVelocity));
        desiredAcceleration = cfg.pid.velocityKp .* ...
            (desiredVelocity - state(4:6));
        
        model = cca.Model.matrices(cfg.robot);
        nu = state(4:6);
        mx = model.effectiveInertia(1, 1);
        my = model.effectiveInertia(2, 2);
        coriolis = [-my * nu(3) * nu(2); ...
                     mx * nu(3) * nu(1); ...
                    (my - mx) * nu(1) * nu(2)];
        friction = cfg.robot.viscousDamping(:) .* nu + ...
            cfg.robot.coulombFriction(:) .* ...
            tanh(nu ./ cfg.robot.frictionSmoothing(:));
        bodyWrench = model.effectiveInertia * desiredAcceleration + ...
            coriolis + friction;
        torque = cca.ControlPrimitives.minimumNormTorque(bodyWrench, cfg);
        end

        function design = designLqr(cfg)
        %DESIGNLQR Local discrete LQR and Riccati stability certificate data.
        
        [A, B] = cca.Model.linearize(zeros(6, 1), zeros(4, 1), ...
            zeros(3, 1), cfg);
        [K, riccatiP, poles] = dlqr(A, B, cfg.cost.Q, cfg.cost.R);
        closedLoop = A - B * K;
        stageMatrix = cfg.cost.Q + K' * cfg.cost.R * K;
        strictSlack = cfg.terminal.slackScale * cfg.cost.Q;
        terminalP = dlyap(closedLoop', stageMatrix + strictSlack);
        
        design.A = A;
        design.B = B;
        design.K = K;
        design.P = terminalP;
        design.riccatiP = riccatiP;
        design.poles = poles;
        design.closedLoop = closedLoop;
        design.dareResidual = closedLoop' * riccatiP * closedLoop ...
            - riccatiP + stageMatrix;
        design.terminalResidual = closedLoop' * terminalP * closedLoop ...
            - terminalP + stageMatrix;
        end

        function terminal = terminalIngredients(cfg)
        %TERMINALINGREDIENTS LQR cost and sampled nonlinear terminal radius.
        
        design = cca.Controllers.designLqr(cfg);
        terminal.P = design.P;
        terminal.sampleCount = 500;
        terminal.decreaseTolerance = 1e-10;
        candidate = localBoundRadius(design, cfg);
        terminal.rho = localCertifiedRadius( ...
            design, cfg, candidate, terminal);
        function rho = localBoundRadius(design, cfg)
        rhoInput = inf;
        for i = 1:4
            gain = design.K(i, :) * (design.P \ design.K(i, :)');
            rhoInput = min(rhoInput, cfg.actuator.torqueMaxNm(i)^2 / gain);
        end
        
        selector = [zeros(3), eye(3)];
        wheelRows = cca.Model.matrices(cfg.robot).wheelKinematics * selector;
        wheelLimit = cca.ControlPrimitives.nmpcWheelSpeedLimit(cfg);
        rhoSpeed = inf;
        for i = 1:4
            gain = wheelRows(i, :) * (design.P \ wheelRows(i, :)');
            rhoSpeed = min(rhoSpeed, ...
                wheelLimit(i)^2 / gain);
        end
        
        deltaMax = cfg.actuator.torqueRateMaxNmps * cfg.timing.sampleTimeS;
        slewRows = design.K * (eye(6) - design.closedLoop);
        rhoSlew = inf;
        for i = 1:4
            gain = slewRows(i, :) * (design.P \ slewRows(i, :)');
            rhoSlew = min(rhoSlew, deltaMax(i)^2 / gain);
        end
        rho = 0.5 * min([rhoInput, rhoSpeed, rhoSlew]);
        end
        
        function rho = localCertifiedRadius(design, cfg, candidate, terminal)
        persistent cachedKey cachedRho
        key = localCacheKey(design, cfg, candidate, terminal);
        if ~isempty(cachedRho) && isequal(cachedKey, key)
            rho = cachedRho;
            return;
        end
        rho = candidate;
        for iteration = 1:20
            decrease = cca.AnalysisTools.terminalDecrease( ...
                design, cfg, rho, terminal.sampleCount);
            slew = cca.AnalysisTools.terminalSlewMargins( ...
                design, cfg, rho, terminal.sampleCount);
            if max(decrease) <= terminal.decreaseTolerance && max(slew) <= 0
                cachedKey = key;
                cachedRho = rho;
                return;
            end
            rho = 0.25 * rho;
        end
        error("cca:control:TerminalCertificate", ...
            "Could not certify a sampled nonlinear terminal radius.");
        end
        
        function key = localCacheKey(design, cfg, candidate, terminal)
        wheelLimit = cca.ControlPrimitives.nmpcWheelSpeedLimit(cfg);
        key = [candidate; terminal.sampleCount; terminal.decreaseTolerance; ...
            cfg.timing.sampleTimeS; cfg.terminal.slackScale; ...
            design.K(:); design.P(:); cfg.actuator.torqueMaxNm(:); ...
            wheelLimit(:)];
        end
        
        end
    end
end

