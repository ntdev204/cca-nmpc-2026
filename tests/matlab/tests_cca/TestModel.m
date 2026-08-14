classdef TestModel < matlab.unittest.TestCase
    methods (Test)
        function powerDuality(testCase)
            cfg = cca.defaults();
            model = cca.Model.matrices(cfg.robot);
            rng(1);
            torque = randn(4, 1);
            twist = randn(3, 1);
            wheelSpeed = model.wheelKinematics * twist;
            wrench = model.bodyWrenchMap * torque;
            testCase.verifyEqual(torque' * wheelSpeed, wrench' * twist, ...
                AbsTol=1e-12);
        end

        function effectiveInertiaAndOverActuation(testCase)
            cfg = cca.defaults();
            model = cca.Model.matrices(cfg.robot);
            testCase.verifyGreaterThan(min(eig(model.effectiveInertia)), 0);
            testCase.verifyEqual(model.inputRank, 3);
            testCase.verifySize(model.inputNullspace, [4, 1]);
            testCase.verifyLessThan(norm( ...
                model.bodyWrenchMap * model.inputNullspace), 1e-12);
        end

        function minimumNormAllocation(testCase)
            cfg = cca.defaults();
            model = cca.Model.matrices(cfg.robot);
            requested = [10; -5; 1];
            torque = cca.ControlPrimitives.minimumNormTorque(requested, cfg);
            testCase.verifyEqual(model.bodyWrenchMap * torque, requested, ...
                AbsTol=1e-12);
            testCase.verifyLessThan(abs( ...
                model.inputNullspace' * torque), 1e-12);
        end

        function rk4Converges(testCase)
            cfg = cca.defaults();
            x0 = [0; 0; 0.2; 0.3; -0.1; 0.15];
            torque = [0.2; -0.1; 0.15; 0.05];
            disturbance = zeros(3, 1);
            coarse = localIntegrate(x0, torque, disturbance, 0.1, 1, cfg);
            medium = localIntegrate(x0, torque, disturbance, 0.05, 2, cfg);
            fine = localIntegrate(x0, torque, disturbance, 0.025, 4, cfg);
            testCase.verifyLessThan(norm(medium - fine), ...
                norm(coarse - fine));
        end
    end
end

function x = localIntegrate(x, torque, disturbance, step, count, cfg)
for k = 1:count
    x = cca.Model.rk4(x, torque, disturbance, step, cfg.robot);
end
end
