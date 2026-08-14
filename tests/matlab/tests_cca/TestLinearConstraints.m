classdef TestLinearConstraints < matlab.unittest.TestCase
    methods (Test)
        function wheelSpeedRowsCoverEverySuccessorIncludingTerminal(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 2;
            cfg.actuator.nmpcWheelSpeedBackoffProgress = [0, 1];
            [matrix, bound] = cca.Nmpc.linearConstraints(zeros(4, 1), cfg);
            wheelMap = cca.Model.matrices(cfg.robot).wheelKinematics;
            wheelProfile = cca.ControlPrimitives.nmpcWheelSpeedProfile(cfg);

            firstRows = 9:12;
            terminalRows = 25:28;
            testCase.verifyEqual(matrix(firstRows, 10:12), wheelMap);
            testCase.verifyEqual(matrix(firstRows, 4:6), zeros(4, 3));
            testCase.verifyEqual(matrix(terminalRows, 16:18), wheelMap);
            testCase.verifyEqual( ...
                bound(firstRows), cfg.actuator.wheelSpeedMaxRadps);
            testCase.verifyEqual( ...
                bound(terminalRows), cfg.actuator.wheelSpeedMaxRadps);
            testCase.verifyEqual( ...
                wheelProfile(:, 1), cfg.actuator.wheelSpeedMaxRadps);
            testCase.verifyEqual( ...
                wheelProfile(:, end), cca.ControlPrimitives.nmpcWheelSpeedLimit(cfg));

            decision = zeros(size(matrix, 2), 1);
            decision(16) = 2 * max(cfg.actuator.wheelSpeedMaxRadps) / ...
                max(abs(wheelMap(:, 1)));
            testCase.verifyGreaterThan(max(matrix * decision - bound), 0);
        end

        function responseSummaryCountsTerminalWheelViolation(testCase)
            cfg = cca.defaults();
            result.controller = "NMPC";
            result.timeS = [0, cfg.timing.sampleTimeS];
            result.states = zeros(6, 2);
            wheelMap = cca.Model.matrices(cfg.robot).wheelKinematics;
            result.states(4, 2) = ...
                2 * max(cfg.actuator.wheelSpeedMaxRadps) / ...
                max(abs(wheelMap(:, 1)));
            result.torques = zeros(4, 1);
            result.solveTimeS = 0;
            result.solverSuccess = true;
            result.fallback = false;
            result.solverConstraintViolation = 0;
            scenario.name = "terminal_speed_fixture";
            scenario.target = [1; 0; 0; 0; 0; 0];
            scenario.projection = [1; 0; 0];
            row = cca.StudyMetrics.summarizeResponse(result, scenario, cfg);
            testCase.verifyEqual(row.WheelViolationRate, 1);
        end
    end
end
