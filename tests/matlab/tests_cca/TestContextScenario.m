classdef TestContextScenario < matlab.unittest.TestCase
    methods (Test)
        function snapshotAccountingIsValid(testCase)
            cfg = cca.defaults();
            scenario = cca.Scenario.crossing();
            nominal = zeros(6, cfg.timing.horizonSteps + 1);
            safety = localPredict(scenario, nominal, cfg);
            problem = cca.Risk.prepare(safety.events, cfg);
            expected = 2 * 2 * cfg.timing.horizonSteps;
            testCase.verifyEqual(problem.eventCount, expected);
            testCase.verifyEqual(problem.humanCount, 2);
            testCase.verifyGreaterThanOrEqual(safety.events.context, 0);
            testCase.verifyLessThanOrEqual(safety.events.context, 1);
        end

        function siblingModesShareContext(testCase)
            cfg = cca.defaults();
            scenario = cca.Scenario.crossing();
            nominal = zeros(6, cfg.timing.horizonSteps + 1);
            safety = localPredict(scenario, nominal, cfg);
            events = safety.events;
            for human = 1:2
                for stage = 1:cfg.timing.horizonSteps
                    group = events.humanIndex == human & ...
                        events.stageIndex == stage;
                    testCase.verifyEqual(numel(unique( ...
                        events.context(group))), 1);
                end
            end
        end

        function closerInteractionScoresHigher(testCase)
            cfg = cca.defaults();
            cfg.timing.horizonSteps = 2;
            events.humanIndex = [1; 1];
            events.stageIndex = [1; 2];
            events.modeIndex = [1; 1];
            events.probability = [1; 1];
            events.context = [0; 0];
            events.omittedMassByGroup = zeros(1, 2);
            nominal = zeros(6, 3);
            positions = [0.4, 2.0; 0, 0];
            velocities = zeros(2, 2);
            scores = cca.score( ...
                nominal, events, positions, velocities, cfg);
            testCase.verifyGreaterThan(scores(1), scores(2));
        end

        function permutationPreservesContextMultiset(testCase)
            cfg = cca.defaults();
            scenario = cca.Scenario.crossing();
            nominal = zeros(6, cfg.timing.horizonSteps + 1);
            baseline = localPredict(scenario, nominal, cfg);
            cfg.context.mode = "permuted";
            permuted = localPredict(scenario, nominal, cfg);
            testCase.verifyEqual(sort(baseline.events.context), ...
                sort(permuted.events.context), AbsTol=1e-14);
            testCase.verifyNotEqual(baseline.events.context, ...
                permuted.events.context);
        end

        function literatureFamiliesExposeMatchedMultimodalEvents(testCase)
            cfg = cca.defaults();
            nominal = zeros(6, cfg.timing.horizonSteps + 1);
            for family = ["circular", "random", "parallel", "multimodal"]
                scenario = cca.Scenario.literatureFamily(family, 3, 17);
                safety = localPredict(scenario, nominal, cfg);
                expected = 3 * 2 * cfg.timing.horizonSteps;
                testCase.verifyEqual( ...
                    numel(safety.events.probability), expected);
                testCase.verifyEqual( ...
                    sum(scenario.modeProbability, 1), ones(1, 3), ...
                    AbsTol=1e-14);
            end
        end

        function contextPositionIsTimeInvariant(testCase)
            cfg = cca.defaults();
            scenario = cca.Scenario.literatureFamily( ...
                "multimodal", 3, 17);
            nominal = zeros(6, cfg.timing.horizonSteps + 1);
            first = localPredict(scenario, nominal, cfg, 0);
            second = localPredict(scenario, nominal, cfg, 5);
            testCase.verifyEqual(first.meanPositionM, second.meanPositionM, ...
                AbsTol=1e-14);
            testCase.verifyEqual(first.meanVelocityMps, second.meanVelocityMps, ...
                AbsTol=1e-14);
        end
    end
end

function safety = localPredict(scenario, nominal, cfg, timeS)
if nargin < 4
    timeS = 0;
end
N = cfg.timing.horizonSteps;
humanCount = size(scenario.contextPositionM, 2);
modeCount = size(scenario.modeVelocityMps, 2);
robotCovariance = repmat( ...
    cfg.safety.robotPositionStdM^2 * eye(2), 1, 1, N);
crossCovariance = zeros(2, 2, humanCount, modeCount, N);
safety = cca.Scenario.predict(scenario, timeS, nominal, cfg, ...
    robotCovariance, crossCovariance);
end
