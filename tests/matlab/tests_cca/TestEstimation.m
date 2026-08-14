classdef TestEstimation < matlab.unittest.TestCase
    methods (Test)
        function ekfPredictionAndUpdateRemainFiniteAndPositive(testCase)
            cfg = cca.defaults();
            measurement = [0.1; -0.2; 0.3; 0.05; -0.04; 0.02];
            filter = cca.Estimator.initialize(measurement, cfg);
            filter = cca.Estimator.predict( ...
                filter, [0.1; -0.05; 0.08; -0.02], cfg);
            filter = cca.Estimator.update( ...
                filter, measurement + 1e-3 * ones(6, 1), cfg);
            testCase.verifyTrue(all(isfinite(filter.mean)));
            testCase.verifyTrue(all(isfinite(filter.covariance), "all"));
            testCase.verifyGreaterThan( ...
                min(eig(filter.covariance)), 0);
        end

        function matchedNoiseIsReproducible(testCase)
            cfg = cca.defaults();
            first = cca.Estimator.measurementNoise(12, cfg);
            second = cca.Estimator.measurementNoise(12, cfg);
            testCase.verifyEqual(first, second);
            testCase.verifyGreaterThan(norm(first, "fro"), 0);
        end

        function scenarioControllerUsesEstimatedState(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 3;
            cfg.study.durationS = 0.10;
            cfg.solver.maxIterations = 10;
            result = cca.Simulation.simulateScenario( ...
                "DETERMINISTIC", cca.Scenario.crossing(), cfg);
            testCase.verifyEqual(result.stateEstimator, "EKF");
            testCase.verifySize(result.estimatedStates, size(result.states));
            testCase.verifySize(result.estimationCovariance, [6, 6, 3]);
            testCase.verifyGreaterThan( ...
                norm(result.estimatedStates - result.states, "fro"), 0);
        end
    end
end
