classdef ControlPrimitives
    methods (Static)
        function torque = minimumNormTorque(bodyWrench, cfg)
            B = cca.Model.matrices(cfg.robot).bodyWrenchMap;
            torque = B' * ((B * B') \ bodyWrench);
        end

        function applied = currentAppliedTorque(plantState, previousCommand)
            if isempty(plantState)
                applied = previousCommand;
            else
                applied = plantState(7:10);
            end
        end

        function torque = limitTorque(requested, previous, cfg)
            deltaMax = cfg.actuator.torqueRateMaxNmps * ...
                cfg.timing.sampleTimeS;
            lower = max(cfg.actuator.torqueMinNm, previous - deltaMax);
            upper = min(cfg.actuator.torqueMaxNm, previous + deltaMax);
            torque = min(upper, max(lower, requested));
        end

        function limit = nmpcWheelSpeedLimit(cfg)
            limit = cfg.actuator.wheelSpeedMaxRadps - ...
                cfg.actuator.nmpcWheelSpeedBackoffRadps;
            assert(all(isfinite(limit) & limit > 0));
        end

        function profile = nmpcWheelSpeedProfile(cfg)
            N = cfg.timing.horizonSteps;
            locked = cfg.actuator.nmpcWheelSpeedBackoffProgress;
            progress = [locked, ones(1, N - numel(locked))];
            profile = cfg.actuator.wheelSpeedMaxRadps - ...
                cfg.actuator.nmpcWheelSpeedBackoffRadps .* progress;
        end

        function reference = regulationReference(target, horizon)
            arguments
                target (6, 1) double {mustBeFinite}
                horizon (1, 1) double {mustBeInteger, mustBePositive}
            end
            reference = repmat(target, 1, horizon + 1);
        end

        function reference = referenceHorizon(current, target, horizon)
            reference = repmat(target(:), 1, horizon + 1);
            poseError = target(1:3) - current(1:3);
            poseError(3) = atan2(sin(poseError(3)), cos(poseError(3)));
            for k = 1:(horizon + 1)
                blend = 1 - exp(-3 * (k - 1) / max(1, horizon));
                reference(1:3, k) = current(1:3) + blend * poseError;
            end
            angleError = reference(3, :) - current(3);
            reference(3, :) = current(3) + ...
                atan2(sin(angleError), cos(angleError));
        end

        function reference = trajectoryReference(timeS, cfg)
            timeS = timeS(:)';
            omega = 2 * pi / cfg.study.trajectoryPeriodS;
            theta = omega * timeS;
            amplitudeX = cfg.study.trajectoryAmplitudeM(1);
            amplitudeY = cfg.study.trajectoryAmplitudeM(2);
            x = amplitudeX * sin(theta);
            y = amplitudeY * sin(2 * theta);
            dx = amplitudeX * omega * cos(theta);
            dy = 2 * amplitudeY * omega * cos(2 * theta);
            ddx = -amplitudeX * omega^2 * sin(theta);
            ddy = -4 * amplitudeY * omega^2 * sin(2 * theta);
            yaw = atan2(dy, dx);
            speedSquared = max(dx .^ 2 + dy .^ 2, 1e-9);
            yawRate = (dx .* ddy - dy .* ddx) ./ speedSquared;
            bodyX = cos(yaw) .* dx + sin(yaw) .* dy;
            bodyY = -sin(yaw) .* dx + cos(yaw) .* dy;
            reference = [x; y; yaw; bodyX; bodyY; yawRate];
        end

        function decision = packDecision(states, torques, relaxation)
            if nargin < 3 || isempty(relaxation)
                decision = [states(:); torques(:)];
            else
                relaxation = relaxation(:);
                assert(numel(relaxation) == size(torques, 2) && ...
                    all(isfinite(relaxation)), ...
                    "cca:control:RelaxationShape", ...
                    "Chance relaxation must contain one finite value per stage.");
                decision = [states(:); torques(:); relaxation];
            end
        end

        function [states, torques, relaxation] = unpackDecision(decision, horizon)
            stateCount = 6 * (horizon + 1);
            baseCount = stateCount + 4 * horizon;
            assert(ismember(numel(decision), [baseCount, baseCount + horizon]), ...
                "cca:control:DecisionShape", ...
                "Expected %d strict or %d relaxed decision variables.", ...
                baseCount, baseCount + horizon);
            states = reshape(decision(1:stateCount), 6, horizon + 1);
            torques = reshape(decision((stateCount + 1):baseCount), ...
                4, horizon);
            if numel(decision) == baseCount
                relaxation = zeros(horizon, 1);
            else
                relaxation = decision((baseCount + 1):end);
            end
        end

        function shifted = shiftWarmStart(states, torques, relaxation)
            shiftedStates = [states(:, 2:end), states(:, end)];
            shiftedTorques = [torques(:, 2:end), torques(:, end)];
            if nargin < 3 || isempty(relaxation)
                shifted = cca.ControlPrimitives.packDecision( ...
                    shiftedStates, shiftedTorques);
            else
                relaxation = relaxation(:);
                shiftedRelaxation = [relaxation(2:end); relaxation(end)];
                shifted = cca.ControlPrimitives.packDecision( ...
                    shiftedStates, shiftedTorques, shiftedRelaxation);
            end
        end
    end
end

