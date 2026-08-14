classdef TestReferenceContract < matlab.unittest.TestCase
    methods (Test)
        function regulationUsesTheSameStepTargetAtEveryStage(testCase)
            target = [1; -0.5; 0.3; 0; 0; 0];
            reference = cca.ControlPrimitives.regulationReference(target, 4);
            testCase.verifyEqual(reference, repmat(target, 1, 5));
        end

        function scenarioReferenceRemainsAnExplicitSharedShaper(testCase)
            current = zeros(6, 1);
            target = [4; 0; 0; 0; 0; 0];
            reference = cca.ControlPrimitives.referenceHorizon(current, target, 4);
            testCase.verifyEqual(reference(:, 1), current);
            testCase.verifyNotEqual(reference(:, end), target);
        end
    end
end
