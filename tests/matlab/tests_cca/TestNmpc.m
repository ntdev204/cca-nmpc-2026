classdef TestNmpc < matlab.unittest.TestCase
    methods (Test)
        function solvesFeasibleHumanFreeProblem(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 4;
            cfg.solver.maxIterations = 15;
            cfg.solver.maxFunctionEvaluations = 3000;
            x0 = zeros(6, 1);
            target = [0.2; 0.1; 0; 0; 0; 0];
            reference = cca.ControlPrimitives.referenceHorizon(x0, target, 4);
            safety.active = false;
            solution = cca.Nmpc.solveNmpc(x0, reference, zeros(4, 1), ...
                safety, "NONE", cfg);
            testCase.verifyTrue(solution.success);
            testCase.verifySize(solution.states, [6, 5]);
            testCase.verifySize(solution.torques, [4, 4]);
            testCase.verifyLessThan(max(abs(solution.torques), [], "all"), ...
                max(cfg.actuator.torqueMaxNm) + 1e-9);
            testCase.verifyLessThanOrEqual(solution.maxConstraintViolation, ...
                cfg.solver.constraintTolerance);
            testCase.verifyFalse(solution.probabilityClaimEligible);
        end

        function terminalConstraintIsRespected(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 3;
            cfg.terminal.enforce = true;
            cfg.solver.maxIterations = 15;
            x0 = zeros(6, 1);
            target = [5e-5; 0; 0; 0; 0; 0];
            reference = cca.ControlPrimitives.referenceHorizon(x0, target, 3);
            safety.active = false;
            solution = cca.Nmpc.solveNmpc(x0, reference, zeros(4, 1), ...
                safety, "NONE", cfg);
            design = cca.Controllers.designLqr(cfg);
            terminal = solution.states(:, end) - reference(:, end);
            terminalTorque = -design.K * terminal;
            switchDelta = terminalTorque - solution.torques(:, end);
            testCase.verifyTrue(solution.success);
            testCase.verifyLessThanOrEqual( ...
                terminal' * design.P * terminal, ...
                cfg.terminal.rho + cfg.solver.constraintTolerance);
            testCase.verifyLessThanOrEqual( ...
                abs(switchDelta), ...
                cfg.actuator.torqueRateMaxNmps * ...
                cfg.timing.sampleTimeS + cfg.solver.constraintTolerance);
        end

        function objectiveGradientMatchesFiniteDifference(testCase)
            [cfg, ~, reference, previous, decision] = localFixture();
            [states, torques] = cca.ControlPrimitives.unpackDecision(decision, 3);
            states(4, 2) = 3;
            decision = cca.ControlPrimitives.packDecision(states, torques);
            [~, gradient] = cca.Nmpc.nmpcObjective( ...
                decision, reference, previous, cfg);
            direction = localDirection(numel(decision));
            step = 1e-6;
            plus = cca.Nmpc.nmpcObjective( ...
                decision + step * direction, reference, previous, cfg);
            minus = cca.Nmpc.nmpcObjective( ...
                decision - step * direction, reference, previous, cfg);
            finiteDifference = (plus - minus) / (2 * step);
            testCase.verifyEqual(gradient' * direction, finiteDifference, ...
                RelTol=1e-6, AbsTol=1e-8);
        end

        function defectJacobianMatchesFiniteDifference(testCase)
            [cfg, x0, reference, previous, decision] = localFixture();
            safety.active = false;
            [~, ~, ~, jacobian] = cca.Nmpc.nmpcConstraints( ...
                decision, x0, reference, previous, ...
                safety, "NONE", cfg);
            direction = localDirection(numel(decision));
            step = 1e-6;
            [~, plus] = cca.Nmpc.nmpcConstraints( ...
                decision + step * direction, x0, reference, previous, ...
                safety, "NONE", cfg);
            [~, minus] = cca.Nmpc.nmpcConstraints( ...
                decision - step * direction, x0, reference, previous, ...
                safety, "NONE", cfg);
            finiteDifference = (plus - minus) / (2 * step);
            testCase.verifyEqual(jacobian' * direction, finiteDifference, ...
                RelTol=2e-5, AbsTol=1e-7);
        end

        function terminalJacobianMatchesFiniteDifference(testCase)
            [cfg, x0, reference, previous, decision] = localFixture();
            cfg.terminal.enforce = true;
            safety.active = false;
            [~, ~, jacobian] = cca.Nmpc.nmpcConstraints( ...
                decision, x0, reference, previous, ...
                safety, "NONE", cfg);
            direction = localDirection(numel(decision));
            step = 1e-6;
            [plus, ~] = cca.Nmpc.nmpcConstraints( ...
                decision + step * direction, x0, reference, previous, ...
                safety, "NONE", cfg);
            [minus, ~] = cca.Nmpc.nmpcConstraints( ...
                decision - step * direction, x0, reference, previous, ...
                safety, "NONE", cfg);
            finiteDifference = (plus - minus) / (2 * step);
            testCase.verifyEqual(jacobian' * direction, finiteDifference, ...
                RelTol=2e-5, AbsTol=1e-7);
        end

        function shootingDefectsUseRobotInertia(testCase)
            [cfg, x0, reference, previous, decision] = localFixture();
            safety.active = false;
            [~, nominalEquality] = cca.Nmpc.nmpcConstraints( ...
                decision, x0, reference, previous, ...
                safety, "NONE", cfg);
            changed = cfg;
            changed.robot.massKg = 1.4 * cfg.robot.massKg;
            changed.robot.yawInertiaKgm2 = ...
                1.3 * cfg.robot.yawInertiaKgm2;
            [~, changedEquality] = cca.Nmpc.nmpcConstraints( ...
                decision, x0, reference, previous, ...
                safety, "NONE", changed);
            testCase.verifyGreaterThan( ...
                norm(changedEquality - nominalEquality), 1e-8);
        end
    end
end

function [cfg, x0, reference, previous, decision] = localFixture()
cfg = cca.defaults();
cfg.timing.horizonSteps = 3;
x0 = [0.1; -0.1; 0.2; 0.05; -0.03; 0.02];
previous = [0.02; -0.01; 0.03; -0.02];
torques = repmat(previous, 1, 3) + 0.01 * reshape(1:12, 4, 3);
states = cca.Model.rollout(x0, torques, zeros(3, 1), ...
    cfg.timing.sampleTimeS, cfg.robot);
reference = cca.ControlPrimitives.referenceHorizon(x0, zeros(6, 1), 3);
decision = cca.ControlPrimitives.packDecision(states, torques);
end

function direction = localDirection(count)
direction = sin((1:count)');
direction = direction / norm(direction);
end
