classdef TestMetrics < matlab.unittest.TestCase
    methods (Test)
        function responseMetricsRetainPositiveAndNegativeExcursions(testCase)
            time = (0:4)';
            positive = [0; -0.1; 0.5; 1.2; 1.0];
            negative = -positive;
            up = cca.AnalysisTools.responseMetrics(time, positive, 1, 0.02);
            down = cca.AnalysisTools.responseMetrics(time, negative, -1, 0.02);
            for metrics = [up, down]
                testCase.verifyEqual( ...
                    metrics.overshootPercent, 20, AbsTol=1e-12);
                testCase.verifyEqual( ...
                    metrics.undershootPercent, 10, AbsTol=1e-12);
                testCase.verifyEqual( ...
                    metrics.maximumAbsoluteError, 1.1, AbsTol=1e-12);
            end
            testCase.verifyEqual(up.responseMinimum, -0.1);
            testCase.verifyEqual(up.responseMaximum, 1.2);
            testCase.verifyEqual(down.responseMinimum, -1.2);
            testCase.verifyEqual(down.responseMaximum, 0.1);
        end

        function nonSettlingResponseStaysUndefined(testCase)
            metrics = cca.AnalysisTools.responseMetrics( ...
                (0:2)', [0; 0.5; 0.8], 1, 0.02);
            testCase.verifyTrue(isnan(metrics.settlingTimeS));
        end

        function nonSolverFieldsAreNotApplicable(testCase)
            cfg = cca.defaults();
            cfg.study.durationS = 0.10;
            result = cca.Simulation.simulate( ...
                "OPEN_LOOP", ones(6, 1), cfg);
            testCase.verifyTrue(all(isnan(result.solveTimeS)));
            testCase.verifyTrue(all(isnan(result.solverSuccess)));
            testCase.verifyTrue(all(isnan(result.fallback)));
            testCase.verifyTrue(all(isnan( ...
                result.solverConstraintViolation)));
            scenario.name = "x";
            scenario.target = ones(6, 1);
            scenario.projection = [1; 0; 0];
            row = cca.StudyMetrics.summarizeResponse(result, scenario, cfg);
            testCase.verifyTrue(isnan(row.SolveP95S));
            testCase.verifyTrue(isnan(row.DeadlineMissRate));
            testCase.verifyTrue(isnan(row.SolverSuccessRate));
            testCase.verifyTrue(isnan(row.FallbackRate));
            testCase.verifyTrue(isnan(row.MaxSolverConstraintViolation));
        end

        function scenarioCompletionRequiresDwell(testCase)
            cfg = cca.defaults();
            sampleCount = 21;
            scenario.target = zeros(6, 1);
            scenario.humanYawRad = 0;
            result = localOutcomeFixture(sampleCount, cfg);
            result.states(1, :) = 1;
            result.states(1, 6) = 0;
            passThrough = cca.AnalysisTools.scenarioOutcome( ...
                result, scenario, cfg);
            testCase.verifyFalse(passThrough.completion);

            result.states(1, :) = 1;
            result.states(1, 6:16) = 0;
            sustained = cca.AnalysisTools.scenarioOutcome( ...
                result, scenario, cfg);
            testCase.verifyTrue(sustained.completion);
            testCase.verifyEqual(sustained.goalTimeS, 0.75);
        end

        function physicalMarginUsesOrientedEllipse(testCase)
            cfg = cca.defaults();
            scenario.target = zeros(6, 1);
            scenario.humanYawRad = 0;
            result = localOutcomeFixture(1, cfg);
            outcome = cca.AnalysisTools.scenarioOutcome( ...
                result, scenario, cfg);
            expected = 1 - cfg.safety.robotRadiusM - ...
                cfg.safety.humanEllipseSemiaxesM(1);
            testCase.verifyEqual( ...
                outcome.minimumPhysicalMarginM, expected, AbsTol=1e-12);
        end

        function wheelBoundaryAndViolationAreSeparated(testCase)
            cfg = cca.defaults();
            tolerance = cfg.solver.constraintTolerance;
            limit = cfg.actuator.wheelSpeedMaxRadps(1);
            result.controller = "OPEN_LOOP";
            result.timeS = [0, cfg.timing.sampleTimeS, ...
                2 * cfg.timing.sampleTimeS];
            result.states = zeros(6, 3);
            result.states(4, 2) = cfg.robot.wheelRadiusM * ...
                (limit + 0.5 * tolerance);
            result.states(4, 3) = cfg.robot.wheelRadiusM * ...
                (limit + 2 * tolerance);
            result.torques = zeros(4, 2);
            result.solveTimeS = nan(1, 2);
            result.solverSuccess = nan(1, 2);
            result.fallback = nan(1, 2);
            result.solverConstraintViolation = nan(1, 2);
            scenario.name = "wheel_boundary";
            scenario.target = zeros(6, 1);
            scenario.projection = [1; 0; 0];
            row = cca.StudyMetrics.summarizeResponse(result, scenario, cfg);
            testCase.verifyEqual(row.WheelActiveRate, 1);
            testCase.verifyEqual(row.WheelViolationRate, 0.5);
            testCase.verifyEqual(row.WheelSpeedExcessPeakRadps, ...
                2 * tolerance, AbsTol=1e-12);
        end
    end
end

function result = localOutcomeFixture(sampleCount, cfg)
result.timeS = (0:(sampleCount - 1)) * cfg.timing.sampleTimeS;
result.states = zeros(6, sampleCount);
result.contextPositionM = [1; 0];
result.target = zeros(6, 1);
end
