classdef TestScenarioControl < matlab.unittest.TestCase
    methods (Test)
        function deterministicSmokeRun(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 3;
            cfg.study.durationS = 0.10;
            cfg.solver.maxIterations = 10;
            scenario = cca.Scenario.crossing();
            result = cca.Simulation.simulateScenario( ...
                "DETERMINISTIC", scenario, cfg);
            testCase.verifySize(result.states, [6, 3]);
            testCase.verifySize(result.torques, [4, 2]);
            testCase.verifyTrue(all(isfinite(result.states), "all"));
        end
    end
end
