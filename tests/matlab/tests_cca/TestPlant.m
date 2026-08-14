classdef TestPlant < matlab.unittest.TestCase
    methods (Test)
        function zeroIsEquilibrium(testCase)
            cfg = cca.defaults();
            next = cca.Plant.step(zeros(10, 1), zeros(4, 1), ...
                zeros(4, 1), zeros(3, 1), cfg);
            testCase.verifyEqual(next, zeros(10, 1), AbsTol=1e-14);
        end

        function actuatorDoesNotJumpToCommand(testCase)
            cfg = cca.defaults();
            command = ones(4, 1);
            next = cca.Plant.step(zeros(10, 1), command, ...
                zeros(4, 1), zeros(3, 1), cfg);
            testCase.verifyGreaterThan(next(7:10), 0);
            testCase.verifyLessThan(next(7:10), command);
        end

        function discrepancyStudyDetectsMismatch(testCase)
            cfg = cca.defaults();
            report = cca.AnalysisTools.modelDiscrepancy(cfg);
            testCase.verifyGreaterThan(report.horizonStateError, 0);
            testCase.verifyGreaterThan(report.maximumPositionErrorM, 0);
            testCase.verifyTrue(all(isfinite(report.plantStates), "all"));
        end

        function lqrRunsOnMismatchedPlant(testCase)
            cfg = cca.defaults();
            cfg.study.plantMode = "mismatched";
            cfg.study.durationS = 0.2;
            result = cca.Simulation.simulate( ...
                "LQR", [0.1; 0; 0; 0; 0; 0], cfg);
            testCase.verifyTrue(all(isfinite(result.states), "all"));
            testCase.verifyGreaterThan(result.states(1, end), 0);
        end

        function cascadedPidBaselineIsFinite(testCase)
            cfg = cca.defaults();
            cfg.study.durationS = 0.4;
            result = cca.Simulation.simulate( ...
                "PID", [0.5; -0.3; 0.2; 0; 0; 0], cfg);
            testCase.verifyTrue(all(isfinite(result.states), "all"));
            upperResidual = result.torques - ...
                repmat(cfg.actuator.torqueMaxNm, ...
                1, size(result.torques, 2));
            testCase.verifyLessThanOrEqual(max(upperResidual, [], "all"), 0);
            testCase.verifyGreaterThan(norm(result.states(1:3, end)), 0);
        end

        function physicalEnvelopeIsFrozenAndContainsHardCases(testCase)
            cases = cca.StudyMetrics.physicalCases("development");
            testCase.verifyEqual(numel(cases), 6);
            testCase.verifyEqual(cases(1).Name, "nominal");
            testCase.verifyEqual(cases(end).Name, "compound_worst");
            testCase.verifyGreaterThan(cases(end).MassScale, 1);
            testCase.verifyGreaterThan(cases(end).ActuatorLagS, 0.05);
            testCase.verifyGreaterThan(cases(end).CommandDelayS, 0);
            testCase.verifyGreaterThan(norm(cases(end).Disturbance), 0);
            validation = cca.StudyMetrics.physicalCases("validation");
            testCase.verifyEqual(numel(validation), 4);
            testCase.verifyFalse(any(ismember( ...
                string({validation.Name}), string({cases.Name}))));
            confirmation = cca.StudyMetrics.physicalCases("confirmation");
            repeated = cca.StudyMetrics.physicalCases("confirmation");
            testCase.verifyEqual(numel(confirmation), 8);
            testCase.verifyEqual(confirmation, repeated);
            testCase.verifyFalse(any(ismember( ...
                string({confirmation.Name}), ...
                [string({cases.Name}), string({validation.Name})])));
        end
    end
end
