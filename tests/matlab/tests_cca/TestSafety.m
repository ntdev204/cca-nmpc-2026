classdef TestSafety < matlab.unittest.TestCase
    methods (Test)
        function ellipseSupportMatchesPrincipalAxes(testCase)
            axes = [0.34; 0.26];
            testCase.verifyEqual( ...
                cca.Safety.ellipseSupport([1; 0], axes, 0), ...
                axes(1), AbsTol=1e-14);
            testCase.verifyEqual( ...
                cca.Safety.ellipseSupport([0; 1], axes, 0), ...
                axes(2), AbsTol=1e-14);
            testCase.verifyEqual( ...
                cca.Safety.ellipseSupport([1; 0], axes, pi / 2), ...
                axes(2), AbsTol=1e-14);
        end

        function ellipseSupportContainsSampledBoundary(testCase)
            axes = [0.34; 0.26];
            yaw = 0.37;
            normal = [cos(-0.81); sin(-0.81)];
            support = cca.Safety.ellipseSupport(normal, axes, yaw);
            angles = linspace(0, 2 * pi, 721);
            rotation = [cos(yaw), -sin(yaw); sin(yaw), cos(yaw)];
            boundary = rotation * diag(axes) * [cos(angles); sin(angles)];
            testCase.verifyLessThanOrEqual( ...
                max(normal' * boundary, [], "all"), support + 1e-12);
        end

        function brakingUsesTorqueAuthority(testCase)
            cfg = cca.defaults();
            state = zeros(6, 1);
            nominal = cca.Safety.brakingAcceleration([1; 0], state, cfg);
            reduced = cfg;
            reduced.actuator.torqueMinNm = ...
                0.5 * cfg.actuator.torqueMinNm;
            reduced.actuator.torqueMaxNm = ...
                0.5 * cfg.actuator.torqueMaxNm;
            lower = cca.Safety.brakingAcceleration([1; 0], state, reduced);
            testCase.verifyGreaterThan(nominal, lower);
            testCase.verifyGreaterThan(lower, 0);
        end

        function chanceRowsHandleMultimodalEvents(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg);
            safety.active = true;
            safety.events = events;
            count = numel(events.probability);
            safety.meanPositionM = 10 * ones(2, count);
            safety.meanVelocityMps = zeros(2, count);
            safety.relativeCovarianceM2 = ...
                repmat(0.01 * eye(2), 1, 1, count);
            safety.separatingDirection = ...
                repmat([-1; -1] / sqrt(2), 1, count);
            states = zeros(6, cfg.timing.horizonSteps + 1);
            rows = cca.Nmpc.chanceRows( ...
                states, safety, "CCA_FIXED_BUDGET", cfg);
            testCase.verifySize(rows, [count, 1]);
            testCase.verifyLessThan(max(rows), 0);
        end

        function chanceGradientMatchesFiniteDifference(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg);
            safety.active = true;
            safety.events = events;
            count = numel(events.probability);
            safety.meanPositionM = repmat([2; 1], 1, count);
            safety.meanVelocityMps = repmat([-0.1; 0.2], 1, count);
            safety.relativeCovarianceM2 = ...
                repmat(0.01 * eye(2), 1, 1, count);
            safety.separatingDirection = ...
                repmat(-[2; 1] / norm([2; 1]), 1, count);
            states = 0.05 * reshape( ...
                sin(1:(6 * (cfg.timing.horizonSteps + 1))), ...
                6, cfg.timing.horizonSteps + 1);
            [~, gradient] = cca.Nmpc.chanceRows( ...
                states, safety, "CCA_FIXED_BUDGET", cfg);
            direction = reshape(cos(1:numel(states)), size(states));
            direction = direction / norm(direction, "fro");
            step = 1e-6;
            plus = cca.Nmpc.chanceRows( ...
                states + step * direction, safety, ...
                "CCA_FIXED_BUDGET", cfg);
            minus = cca.Nmpc.chanceRows( ...
                states - step * direction, safety, ...
                "CCA_FIXED_BUDGET", cfg);
            finiteDifference = (plus - minus) / (2 * step);
            testCase.verifyEqual(gradient' * direction(:), ...
                finiteDifference, RelTol=2e-5, AbsTol=1e-7);
        end

        function chanceRowUsesDirectRelativeCovariance(testCase)
            cfg = cca.defaults();
            safety.meanPositionM = [2; 0];
            safety.meanVelocityMps = zeros(2, 1);
            safety.separatingDirection = [-1; 0];
            safety.relativeCovarianceM2 = 0.0101 * eye(2);
            state = zeros(6, 1);
            narrow = cca.Nmpc.chanceRow( ...
                state, safety, 0.01, 1, cfg);
            safety.relativeCovarianceM2 = 0.05 * eye(2);
            wide = cca.Nmpc.chanceRow( ...
                state, safety, 0.01, 1, cfg);
            testCase.verifyGreaterThan(wide, narrow);
        end

        function chanceRowHandlesZeroAndNearSingularCovariance(testCase)
            cfg = cca.defaults();
            safety.meanPositionM = [4; 0];
            safety.meanVelocityMps = zeros(2, 1);
            safety.separatingDirection = [-1; 0];
            safety.relativeCovarianceM2 = zeros(2);
            zeroVariance = cca.Nmpc.chanceRow( ...
                zeros(6, 1), safety, 0.01, 1, cfg);
            safety.relativeCovarianceM2 = ...
                [1e-12, 1e-12; 1e-12, 1e-12];
            nearSingular = cca.Nmpc.chanceRow( ...
                zeros(6, 1), safety, 0.01, 1, cfg);
            testCase.verifyTrue(isfinite(zeroVariance));
            testCase.verifyTrue(isfinite(nearSingular));
            testCase.verifyGreaterThanOrEqual(nearSingular, zeroVariance);
        end

        function chanceRowRejectsInvalidRelativeCovariance(testCase)
            cfg = cca.defaults();
            safety.meanPositionM = [4; 0];
            safety.meanVelocityMps = zeros(2, 1);
            safety.separatingDirection = [-1; 0];
            safety.relativeCovarianceM2 = [0.01, 0; 0.001, 0.01];
            testCase.verifyError( ...
                @() cca.Nmpc.chanceRow(zeros(6, 1), safety, 0.01, 1, cfg), ...
                "cca:control:RelativeCovarianceSymmetry");
            safety.relativeCovarianceM2 = [-0.001, 0; 0, 0.01];
            testCase.verifyError( ...
                @() cca.Nmpc.chanceRow(zeros(6, 1), safety, 0.01, 1, cfg), ...
                "cca:control:RelativeCovariancePsd");
        end

        function relaxationSubtractsXiByStage(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg);
            count = numel(events.probability);
            safety.active = true;
            safety.events = events;
            safety.meanPositionM = repmat([4; 0], 1, count);
            safety.meanVelocityMps = zeros(2, count);
            safety.relativeCovarianceM2 = ...
                repmat(0.01 * eye(2), 1, 1, count);
            safety.separatingDirection = repmat([-1; 0], 1, count);
            states = zeros(6, cfg.timing.horizonSteps + 1);
            strict = cca.Nmpc.chanceRows( ...
                states, safety, "CCA_FIXED_BUDGET", cfg);
            xi = linspace(0.01, 0.10, cfg.timing.horizonSteps)';
            relaxed = cca.Nmpc.chanceRows( ...
                states, safety, "CCA_FIXED_BUDGET", cfg, xi);
            expected = repelem(xi, 2);
            testCase.verifyEqual(strict - relaxed, expected, AbsTol=1e-14);
        end
    end
end

function events = localEvents(cfg)
N = cfg.timing.horizonSteps;
events.humanIndex = ones(2 * N, 1);
events.stageIndex = repelem((1:N)', 2);
events.modeIndex = repmat([1; 2], N, 1);
events.probability = repmat([0.6; 0.4], N, 1);
events.context = repelem(linspace(0.2, 0.8, N)', 2);
events.omittedMassByGroup = zeros(1, N);
end
