classdef TestPositionState < matlab.unittest.TestCase
    methods (Test)
        function positionStepUsesSixStateBodyVelocity(testCase)
            x = zeros(6, 1);
            command = [0.4; 0.1; 0.2];
            next = cca.Model.positionStep(x, command, 0.1, 0.08);
            testCase.verifySize(next, [6, 1]);
            testCase.verifyGreaterThan(next(1), 0);
            testCase.verifyGreaterThan(next(2), 0);
            testCase.verifyEqual(next(4:6), command, AbsTol=1e-12);
        end

        function positionSimulationExposesContract(testCase)
            cfg = cca.defaults();
            cfg.study.durationS = 0.25;
            result = cca.Simulation.simulatePosition( ...
                "CCA_NMPC", [1; 0; 0; 0; 0; 0], cfg);
            testCase.verifyEqual(result.controlMode, "position_state");
            testCase.verifySize(result.states, [6, 6]);
            testCase.verifySize(result.commands, [3, 5]);
            testCase.verifyTrue(all(isfinite(result.states), "all"));
            testCase.verifyTrue(all(isfinite(result.commands), "all"));
        end

        function positionExportWritesOnlyPositionStateContract(testCase)
            cfg = cca.defaults();
            cfg.study.durationS = 0.25;
            study = cca.StudyRunner.runPositionState(cfg);
            output = fullfile(tempdir, "cca_position_export_" + string(char(java.util.UUID.randomUUID())));
            cleanup = onCleanup(@() rmdir(output, "s"));
            artifacts = cca.StudyIO.exportPositionState(study, cfg, output);
            testCase.verifyGreaterThanOrEqual(numel(artifacts), 2);
            testCase.verifyTrue(isfile(fullfile(output, "manifest.json")));
            testCase.verifyTrue(isfile(fullfile(output, "tables", ...
                "position_state_summary.csv")));
            manifest = jsondecode(fileread(fullfile(output, "manifest.json")));
            testCase.verifyEqual(string(manifest.controlMode), "position_state");
            testCase.verifyEqual(string(manifest.controlInterface), "body_velocity");
            testCase.verifyFalse(manifest.paperEdit);
            testCase.verifyFalse(any(contains(string({manifest.artifacts.path}), ...
                "torque", IgnoreCase=true)));
        end
    end
end
