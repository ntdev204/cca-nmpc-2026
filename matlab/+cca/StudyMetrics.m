classdef StudyMetrics
    methods (Static)
        function gates = buildAcceptanceTable(results)
        %BUILDACCEPTANCETABLE Locked offline MATLAB numerical gates.
        
        dev = localNmpcRows(results.robustnessDevelopment.summary);
        confirmation = localNmpcRows(results.robustnessConfirmation.summary);
        trajectory = results.trajectoryTracking.summary( ...
            results.trajectoryTracking.summary.Controller == "NMPC", :);
        names = [
            "continuous_and_discrete_controllability"
            "zoh_cross_check"
            "local_terminal_certificate"
            "sampled_two_step_feasibility"
            "numerical_integration_parity"
            "development_constraint_transfer"
            "confirmation_constraint_transfer"
            "ekf_state_estimation"
            "trajectory_tracking"
            "matlab_gate_a_numerical"
        ];
        pass = [
            results.openLoop.ContinuousControllabilityRank == 6 && ...
                results.openLoop.DiscreteControllabilityRank == 6
            results.openLoop.ZohParityPass
            results.stability.pass
            results.localNmpcStability.Pass
            results.numericalParity.pass
            localRobustnessPass(dev)
            localRobustnessPass(confirmation)
            localEstimatorPass(results, trajectory)
            localTrajectoryPass(trajectory)
            false
        ];
        pass(end) = all(pass(1:(end - 1)));
        scope = repmat("synthetic offline MATLAB", size(names));
        scope(3) = "nominal local terminal certificate";
        scope(4) = "sampled local feasibility; no recursive-feasibility proof";
        scope(7) = "seed 27072027 held-out synthetic envelope";
        scope(8) = "synthetic noisy pose and body-velocity observations";
        scope(9) = "figure-eight tracking with six-state EKF feedback";
        gates = table(names, logical(pass), scope, ...
            VariableNames=["Gate", "Pass", "Scope"]);
        function pass = localEstimatorPass(results, trajectory)
        scenario = results.stochastic.summary;
        pass = all(isfinite(scenario.EstimatorPositionRmseM)) && ...
            all(isfinite(scenario.EstimatorYawRmseRad)) && ...
            all(isfinite(scenario.EstimatorVelocityRmse)) && ...
            trajectory.EstimatorPositionRmseM <= 0.05 && ...
            trajectory.EstimatorYawRmseRad <= deg2rad(2);
        end
        
        function pass = localTrajectoryPass(row)
        pass = all(isfinite([row.PositionRmseM, row.PositionMaxErrorM, ...
            row.YawRmseRad, row.VelocityRmse])) && ...
            row.PositionRmseM <= 0.35 && row.PositionMaxErrorM <= 0.75 && ...
            row.WheelViolationRate == 0;
        end
        
        function rows = localNmpcRows(summary)
        rows = summary(summary.Controller == "NMPC", :);
        end
        
        function pass = localRobustnessPass(rows)
        pass = all(isfinite(rows.SettlingTimeS)) && ...
            all(rows.SolverSuccessRate == 1) && all(rows.FallbackRate == 0) && ...
            all(rows.MaxSolverConstraintViolation <= 1e-6) && ...
            all(rows.WheelViolationRate == 0) && ...
            all(rows.WheelSpeedExcessPeakRadps <= 1e-6);
        end
        
        end

        function comparison = buildCcaComparisonTable(results)
        %BUILDCCACOMPARISONTABLE Main crossing and context-ablation rows.
        
        main = results.stochastic.summary;
        main.Study = repmat("main_crossing", height(main), 1);
        main.ContextMode = repmat("nominal", height(main), 1);
        main = movevars(main, ["Study", "ContextMode"], Before=1);
        ablation = results.contextAblation.summary;
        ablation.Study = repmat("context_ablation", height(ablation), 1);
        ablation = movevars(ablation, ["Study", "ContextMode"], Before=1);
        comparison = [main; ablation];
        end

        function certificate = buildCertificateTable(results)
        %BUILDCERTIFICATETABLE Normalize heterogeneous mathematical evidence.
        
        items = {
            "open_loop", results.openLoop
            "open_loop_channel", results.openLoopChannels
            "open_loop_pulse", results.openLoopPulseChannels
            "over_actuation", results.overActuation
            "feedback_necessity", results.feedbackNecessity.summary
            "stability", results.stability
            "empirical_roa", results.regionOfAttraction
            "local_nmpc", results.localNmpcStability
            "numerical_parity", results.numericalParity
            "model_discrepancy", results.modelDiscrepancy
        };
        parts = cell(size(items, 1), 1);
        for i = 1:size(items, 1)
            parts{i} = localLongForm(items{i, 1}, items{i, 2});
        end
        certificate = vertcat(parts{:});
        function long = localLongForm(source, input)
        rowCount = height(input);
        variableCount = width(input);
        count = rowCount * variableCount;
        sources = repmat(string(source), count, 1);
        rows = zeros(count, 1);
        metrics = strings(count, 1);
        values = strings(count, 1);
        index = 0;
        for row = 1:rowCount
            for variable = 1:variableCount
                index = index + 1;
                rows(index) = row;
                metrics(index) = input.Properties.VariableNames{variable};
                values(index) = localValue(input{row, variable});
            end
        end
        long = table(sources, rows, metrics, values, ...
            VariableNames=["Evidence", "EvidenceRow", "Metric", "Value"]);
        end
        
        function text = localValue(value)
        if isnumeric(value) || islogical(value)
            if isscalar(value)
                text = string(sprintf("%.17g", double(value)));
            else
                text = string(mat2str(value, 17));
            end
        elseif isstring(value)
            text = join(value, ";");
        elseif ischar(value)
            text = string(value);
        elseif iscell(value)
            text = join(string(value), ";");
        else
            text = string(value);
        end
        end
        
        end

        function cases = physicalCases(envelope)
        if nargin < 1
            envelope = "development";
        end
        make = @localCase;
        switch upper(string(envelope))
            case "DEVELOPMENT"
                cases(1) = make("nominal", "nominal", 1.00, 1.00, 1.00, 1.00, 0.00, 0.00, [0; 0; 0]);
                cases(2) = make("heavy_high_loss", "mismatched", 1.15, 1.10, 1.25, 1.25, 0.06, 0.03, [0.50; -0.30; 0.05]);
                cases(3) = make("light_low_loss", "mismatched", 0.85, 0.90, 0.75, 0.75, 0.02, 0.00, [-0.40; 0.25; -0.04]);
                cases(4) = make("lag_delay", "mismatched", 1.00, 1.00, 1.00, 1.00, 0.08, 0.05, [0.30; 0.30; 0.08]);
                cases(5) = make("yaw_disturbance", "mismatched", 1.00, 0.75, 1.10, 1.10, 0.05, 0.03, [0.10; -0.10; 0.15]);
                cases(6) = make("compound_worst", "mismatched", 1.20, 0.80, 1.30, 1.30, 0.08, 0.05, [0.70; -0.50; 0.10]);
            case "VALIDATION"
                cases(1) = make("mid_cross", "mismatched", 1.10, 0.95, 1.15, 0.90, 0.070, 0.040, [0.55; 0.15; -0.08]);
                cases(2) = make("light_delay", "mismatched", 0.90, 1.05, 0.85, 1.20, 0.070, 0.040, [-0.30; -0.40; 0.12]);
                cases(3) = make("heavy_low_loss", "mismatched", 1.18, 0.85, 0.80, 0.80, 0.040, 0.020, [0.60; -0.20; 0.05]);
                cases(4) = make("mixed_compound", "mismatched", 1.12, 0.78, 1.28, 0.82, 0.075, 0.045, [-0.65; 0.45; -0.12]);
            case "CONFIRMATION"
                sampleCount = 8;
                stream = RandStream("mt19937ar", Seed=27072027);
                unit = rand(stream, sampleCount, 9);
                lower = [0.85, 0.75, 0.75, 0.75, 0.02, 0.00, -0.70, -0.50, -0.15];
                upperBound = [1.20, 1.10, 1.30, 1.30, 0.08, 0.05, 0.70, 0.50, 0.15];
                sample = lower + unit .* (upperBound - lower);
                for i = sampleCount:-1:1
                    cases(i) = make(compose("confirmation_%02d", i), "mismatched", ...
                        sample(i, 1), sample(i, 2), sample(i, 3), sample(i, 4), ...
                        sample(i, 5), sample(i, 6), sample(i, 7:9)');
                end
            otherwise
                error("cca:study:Envelope", "Unknown envelope %s.", envelope);
        end
        function item = localCase(name, mode, mass, inertia, viscous, coulomb, lag, delay, disturbance)
        item.Name = name;
        item.PlantMode = mode;
        item.MassScale = mass;
        item.YawInertiaScale = inertia;
        item.ViscousDampingScale = viscous;
        item.CoulombFrictionScale = coulomb;
        item.ActuatorLagS = lag;
        item.CommandDelayS = delay;
        item.Disturbance = disturbance;
        end
        
        end

        function row = summarizeResponse(result, scenario, cfg)
        %SUMMARIZERESPONSE One matched closed-loop response row.
        
        pose = result.states(1:3, :);
        primary = scenario.projection' * pose;
        target = scenario.projection' * scenario.target(1:3);
        metrics = cca.AnalysisTools.responseMetrics( ...
            result.timeS, primary, target, cfg.study.settleBandFraction);
        
        desiredPose = scenario.target(1:3);
        error = desiredPose - pose;
        error(3, :) = atan2(sin(error(3, :)), cos(error(3, :)));
        projector = eye(3) - scenario.projection * scenario.projection';
        crossAxis = vecnorm(projector * error);
        torqueNorm = vecnorm(result.torques);
        delta = diff([zeros(4, 1), result.torques], 1, 2);
        nullVector = cca.Model.matrices(cfg.robot).inputNullspace;
        nullTorque = abs(nullVector' * result.torques);
        wheel = cca.Model.matrices(cfg.robot).wheelKinematics * ...
            result.states(4:6, 2:end);
        wheelExcess = abs(wheel) - cfg.actuator.wheelSpeedMaxRadps;
        torqueActive = mean(any(abs(result.torques) >= ...
            0.99 * cfg.actuator.torqueMaxNm, 1));
        slewLimit = cfg.actuator.torqueRateMaxNmps * cfg.timing.sampleTimeS;
        slewActive = mean(any(abs(delta) >= 0.99 * slewLimit, 1));
        wheelActive = mean(any(wheelExcess >= ...
            -cfg.solver.constraintTolerance, 1));
        wheelViolation = mean(any(wheelExcess > ...
            cfg.solver.constraintTolerance, 1));
        wheelExcessPeak = max([0; wheelExcess(:)]);
        [estimatorPositionRmse, estimatorYawRmse, estimatorVelocityRmse] = ...
            localEstimatorMetrics(result);
        
        row = table( ...
            scenario.name, result.controller, metrics.riseTimeS, ...
            metrics.settlingTimeS, metrics.overshootPercent, ...
            metrics.undershootPercent, metrics.responseMinimum, ...
            metrics.responseMaximum, metrics.maximumAbsoluteError, ...
            metrics.steadyStateError, metrics.IAE, metrics.ISE, metrics.ITAE, ...
            sqrt(mean(torqueNorm .^ 2)), max(torqueNorm), ...
            max(abs(delta), [], "all") / cfg.timing.sampleTimeS, ...
            max(crossAxis), sqrt(mean(nullTorque .^ 2)), ...
            torqueActive, slewActive, wheelActive, wheelViolation, wheelExcessPeak, ...
            localPercentile(result.solveTimeS, 50), ...
            localPercentile(result.solveTimeS, 95), ...
            localPercentile(result.solveTimeS, 99), ...
            max(result.solveTimeS), ...
            localDeadlineMissRate( ...
                result.solveTimeS, cfg.timing.sampleTimeS), ...
            mean(result.solverSuccess), mean(result.fallback), ...
            max(result.solverConstraintViolation), ...
            estimatorPositionRmse, estimatorYawRmse, estimatorVelocityRmse, ...
            VariableNames=["Scenario", "Controller", "RiseTimeS", ...
            "SettlingTimeS", "OvershootPercent", "UndershootPercent", ...
            "ResponseMinimum", "ResponseMaximum", "MaximumAbsoluteError", ...
            "SteadyStateError", "IAE", "ISE", "ITAE", ...
            "TorqueRmsNm", "TorquePeakNm", ...
            "TorqueSlewPeakNmps", "CrossAxisPeak", "NullTorqueRmsNm", ...
            "TorqueActiveRate", "SlewActiveRate", "WheelActiveRate", ...
            "WheelViolationRate", "WheelSpeedExcessPeakRadps", ...
            "SolveP50S", "SolveP95S", "SolveP99S", "SolveMaxS", ...
            "DeadlineMissRate", "SolverSuccessRate", "FallbackRate", ...
            "MaxSolverConstraintViolation", "EstimatorPositionRmseM", ...
            "EstimatorYawRmseRad", "EstimatorVelocityRmse"]);
        function [positionRmse, yawRmse, velocityRmse] = ...
            localEstimatorMetrics(result)
        if ~isfield(result, "estimatedStates")
            positionRmse = NaN;
            yawRmse = NaN;
            velocityRmse = NaN;
            return;
        end
        error = result.estimatedStates - result.states;
        error(3, :) = atan2(sin(error(3, :)), cos(error(3, :)));
        positionRmse = sqrt(mean(sum(error(1:2, :) .^ 2, 1)));
        yawRmse = sqrt(mean(error(3, :) .^ 2));
        velocityRmse = sqrt(mean(sum(error(4:6, :) .^ 2, 1)));
        end
        
        function value = localDeadlineMissRate(values, deadline)
        valid = isfinite(values);
        if any(valid)
            value = mean(values(valid) > deadline);
        else
            value = NaN;
        end
        end
        
        function value = localPercentile(values, percentile)
        values = sort(values(:));
        if isempty(values)
            value = NaN;
            return;
        end
        index = max(1, ceil(percentile / 100 * numel(values)));
        value = values(index);
        end
        
        end

        function row = summarizeScenario(result, cfg)
        %SUMMARIZESCENARIO One stochastic closed-loop comparison row.
        
        torqueNorm = vecnorm(result.torques);
        delta = diff([zeros(4, 1), result.torques], 1, 2);
        wheel = cca.Model.matrices(cfg.robot).wheelKinematics * ...
            result.states(4:6, 2:end);
        wheelExcess = abs(wheel) - cfg.actuator.wheelSpeedMaxRadps;
        wheelActive = mean(any(wheelExcess >= ...
            -cfg.solver.constraintTolerance, 1));
        wheelViolation = mean(any(wheelExcess > ...
            cfg.solver.constraintTolerance, 1));
        wheelExcessPeak = max([0; wheelExcess(:)]);
        [estimatorPositionRmse, estimatorYawRmse, estimatorVelocityRmse] = ...
            localEstimatorMetrics(result);
        row = table(result.controller, result.collision, result.unsafeIntrusion, ...
            result.completion, result.goalTimeS, result.minimumPhysicalMarginM, ...
            sqrt(mean(torqueNorm .^ 2)), ...
            localPercentile(result.solveTimeS, 50), ...
            localPercentile(result.solveTimeS, 95), ...
            localPercentile(result.solveTimeS, 99), ...
            max(result.solveTimeS), ...
            mean(result.solveTimeS > cfg.timing.sampleTimeS), ...
            mean(result.solverSuccess), ...
            mean(result.fallback), max(result.solverConstraintViolation), ...
            max(abs(delta), [], "all") / cfg.timing.sampleTimeS, ...
            wheelActive, wheelViolation, wheelExcessPeak, ...
            result.contextCalibrationValid, ...
            estimatorPositionRmse, estimatorYawRmse, estimatorVelocityRmse, ...
            VariableNames=["Controller", "Collision", "UnsafeIntrusion", ...
            "Completion", "GoalTimeS", "MinimumPhysicalMarginM", ...
            "TorqueRmsNm", "SolveP50S", "SolveP95S", "SolveP99S", ...
            "SolveMaxS", "DeadlineMissRate", "SolverSuccessRate", "FallbackRate", ...
            "MaxSolverConstraintViolation", "TorqueSlewPeakNmps", ...
            "WheelActiveRate", "WheelViolationRate", ...
            "WheelSpeedExcessPeakRadps", "ContextCalibrationValid", ...
            "EstimatorPositionRmseM", "EstimatorYawRmseRad", ...
            "EstimatorVelocityRmse"]);
        function [positionRmse, yawRmse, velocityRmse] = ...
            localEstimatorMetrics(result)
        if ~isfield(result, "estimatedStates")
            positionRmse = NaN;
            yawRmse = NaN;
            velocityRmse = NaN;
            return;
        end
        error = result.estimatedStates - result.states;
        error(3, :) = atan2(sin(error(3, :)), cos(error(3, :)));
        positionRmse = sqrt(mean(sum(error(1:2, :) .^ 2, 1)));
        yawRmse = sqrt(mean(error(3, :) .^ 2));
        velocityRmse = sqrt(mean(sum(error(4:6, :) .^ 2, 1)));
        end
        
        function value = localPercentile(values, percentile)
        values = sort(values(:));
        index = max(1, ceil(percentile / 100 * numel(values)));
        value = values(index);
        end
        
        end

        function row = summarizeTrajectory(result, cfg)
        %SUMMARIZETRAJECTORY Tracking, estimation, actuation and solver metrics.
        
        trackingError = result.states - result.desiredStates;
        trackingError(3, :) = atan2( ...
            sin(trackingError(3, :)), cos(trackingError(3, :)));
        positionError = vecnorm(trackingError(1:2, :));
        velocityError = vecnorm(trackingError(4:6, :));
        estimationError = result.estimatedStates - result.states;
        estimationError(3, :) = atan2( ...
            sin(estimationError(3, :)), cos(estimationError(3, :)));
        torqueNorm = vecnorm(result.torques);
        wheel = cca.Model.matrices(cfg.robot).wheelKinematics * ...
            result.states(4:6, 2:end);
        wheelExcess = abs(wheel) - cfg.actuator.wheelSpeedMaxRadps;
        
        row = table(result.controller, ...
            sqrt(mean(positionError .^ 2)), max(positionError), ...
            sqrt(mean(trackingError(3, :) .^ 2)), ...
            sqrt(mean(velocityError .^ 2)), ...
            sqrt(mean(sum(estimationError(1:2, :) .^ 2, 1))), ...
            sqrt(mean(estimationError(3, :) .^ 2)), ...
            sqrt(mean(sum(estimationError(4:6, :) .^ 2, 1))), ...
            sqrt(mean(torqueNorm .^ 2)), max(abs(wheel), [], "all"), ...
            mean(any(wheelExcess > cfg.solver.constraintTolerance, 1)), ...
            localPercentile(result.solveTimeS, 95), ...
            localDeadlineMissRate(result.solveTimeS, cfg.timing.sampleTimeS), ...
            mean(result.solverSuccess, "omitnan"), ...
            mean(result.fallback, "omitnan"), ...
            max(result.solverConstraintViolation, [], "omitnan"), ...
            VariableNames=["Controller", "PositionRmseM", ...
            "PositionMaxErrorM", "YawRmseRad", "VelocityRmse", ...
            "EstimatorPositionRmseM", "EstimatorYawRmseRad", ...
            "EstimatorVelocityRmse", "TorqueRmsNm", ...
            "PeakWheelSpeedRadps", "WheelViolationRate", "SolveP95S", ...
            "DeadlineMissRate", "SolverSuccessRate", "FallbackRate", ...
            "MaxSolverConstraintViolation"]);
        function value = localDeadlineMissRate(values, deadline)
        valid = isfinite(values);
        if any(valid)
            value = mean(values(valid) > deadline);
        else
            value = NaN;
        end
        end
        
        function value = localPercentile(values, percentile)
        values = sort(values(isfinite(values)));
        if isempty(values)
            value = NaN;
            return;
        end
        index = max(1, ceil(percentile / 100 * numel(values)));
        value = values(index);
        end
        
        end
    end
end

