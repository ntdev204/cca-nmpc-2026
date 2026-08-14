classdef TestTrajectory < matlab.unittest.TestCase
    methods (Test)
        function figureEightReferenceIsFiniteAndPeriodic(testCase)
            cfg = cca.defaults();
            time = [0, cfg.study.trajectoryPeriodS];
            reference = cca.ControlPrimitives.trajectoryReference(time, cfg);
            testCase.verifySize(reference, [6, 2]);
            testCase.verifyTrue(all(isfinite(reference), "all"));
            testCase.verifyEqual(reference(1:2, 1), ...
                reference(1:2, 2), AbsTol=1e-12);
        end

        function lqrTrajectorySmokeRunUsesEkf(testCase)
            cfg = cca.defaults();
            cfg.study.trajectoryDurationS = 0.10;
            result = cca.Simulation.simulateTrajectory("LQR", cfg);
            testCase.verifySize(result.states, [6, 3]);
            testCase.verifySize(result.desiredStates, [6, 3]);
            testCase.verifyEqual(result.stateEstimator, "EKF");
            testCase.verifyTrue(all(isfinite(result.states), "all"));
        end
    end
end
