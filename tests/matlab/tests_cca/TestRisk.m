classdef TestRisk < matlab.unittest.TestCase
    methods (Test)
        function domainSumOrderingAndQuantileDirection(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 3);
            result = cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg);
            testCase.verifyGreaterThanOrEqual( ...
                result.epsilonByGroup, cfg.risk.epsilonMin);
            testCase.verifyLessThan(result.epsilonByGroup, 0.5);
            testCase.verifyEqual(sum(result.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);
            testCase.verifyLessThan(diff(result.epsilonByGroup), 0);
            quantile = sqrt(2) * erfcinv(2 * result.epsilonByGroup);
            testCase.verifyGreaterThan(diff(quantile), 0);
        end

        function uniformIsExact(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 3);
            result = cca.Risk.allocate("UNIFORM", events, cfg);
            expected = cfg.risk.barEpsilon / cfg.timing.horizonSteps;
            testCase.verifyEqual(result.epsilonByGroup, ...
                expected * ones(cfg.timing.horizonSteps, 1), ...
                AbsTol=1e-14);
            testCase.verifyFalse(result.softmaxClipped);
        end

        function ccaBetaZeroIsUniformSpecialCase(testCase)
            cfg = cca.defaults();
            cfg.risk.contextBeta = 0;
            events = localEvents(cfg, 3);
            result = cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg);
            expected = cfg.risk.barEpsilon / cfg.timing.horizonSteps;
            testCase.verifyEqual(result.epsilonByGroup, ...
                expected * ones(cfg.timing.horizonSteps, 1), ...
                AbsTol=1e-14);
            testCase.verifyFalse(result.softmaxClipped);
        end

        function equalContextsAreSymmetric(testCase)
            cfg = cca.defaults();
            cfg.risk.epsilonMin = 1e-3;
            cfg.risk.contextBeta = 17;
            events = localContextEvents(cfg, 0.37 * ones(4, 1), 3);
            result = cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg);
            testCase.verifyEqual(result.weights, 0.25 * ones(4, 1), ...
                AbsTol=0);
            testCase.verifyEqual(result.epsilonByGroup, ...
                (cfg.risk.barEpsilon / 4) * ones(4, 1), AbsTol=1e-14);
        end

        function allocationIsContinuousForFixedActiveSet(testCase)
            cfg = cca.defaults();
            context = [0.15; 0.45; 0.80];
            baseline = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                localContextEvents(cfg, context, 3), cfg);
            residualBudget = cfg.risk.barEpsilon - ...
                numel(context) * cfg.risk.epsilonMin;
            for step = [1e-2, 1e-4, 1e-6]
                perturbedContext = context;
                perturbedContext(2) = perturbedContext(2) + step;
                perturbed = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                    localContextEvents(cfg, perturbedContext, 3), cfg);
                observed = max(abs(perturbed.epsilonByGroup - ...
                    baseline.epsilonByGroup));
                bound = residualBudget * cfg.risk.contextBeta * step / 4;
                testCase.verifyLessThanOrEqual(observed, ...
                    bound * (1 + 1e-12));
            end
        end

        function activeSetChangeIsGlobalContinuityCounterexample(testCase)
            cfg = cca.defaults();
            twoGroups = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                localContextEvents(cfg, [0.2; 0.8], 3), cfg);
            threeGroups = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                localContextEvents(cfg, [0.2; 0.8; 0.5], 3), cfg);
            jump = abs(threeGroups.epsilonByGroup(1:2) - ...
                twoGroups.epsilonByGroup);
            testCase.verifyGreaterThan(max(jump), 1e-3);
            testCase.verifyEqual(sum(twoGroups.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);
            testCase.verifyEqual(sum(threeGroups.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);
        end

        function permutationEquivariance(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 3);
            baseline = cca.Risk.allocate( ...
                "CCA_FIXED_BUDGET", events, cfg);
            rng(17);
            permutation = randperm(numel(events.probability));
            permuted = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                localPermute(events, permutation), cfg);
            restored = zeros(size(permuted.conditionalEpsilon));
            restored(permutation) = permuted.conditionalEpsilon;
            testCase.verifyEqual(restored, ...
                baseline.conditionalEpsilon, AbsTol=1e-14);
        end

        function shiftedSoftmaxIsNumericallyStable(testCase)
            cfg = cca.defaults();
            cfg.risk.contextBeta = 1e6;
            result = cca.Risk.allocate("CCA_FIXED_BUDGET", ...
                localEvents(cfg, 2), cfg);
            testCase.verifyTrue(all(isfinite(result.weights)));
            testCase.verifyEqual(sum(result.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);
            testCase.verifyTrue(result.softmaxClipped);
        end

        function validParameterBoundariesRemainFinite(testCase)
            cfg = cca.defaults();
            events = localContextEvents(cfg, [0; 0.5; 1], 3);
            cfg.risk.epsilonMin = 0;
            cfg.risk.barEpsilon = 0.5 - eps(0.5);
            first = cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg);
            testCase.verifyTrue(all(isfinite(first.weights)));
            testCase.verifyTrue(all(isfinite(first.epsilonByGroup)));
            testCase.verifyGreaterThanOrEqual(first.epsilonByGroup, 0);
            testCase.verifyEqual(sum(first.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);

            cfg.risk.barEpsilon = 0.05;
            cfg.risk.epsilonMin = ...
                cfg.risk.barEpsilon / 3 - eps(cfg.risk.barEpsilon / 3);
            second = cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg);
            testCase.verifyTrue(all(isfinite(second.epsilonByGroup)));
            testCase.verifyGreaterThanOrEqual(second.epsilonByGroup, ...
                cfg.risk.epsilonMin);
            testCase.verifyEqual(sum(second.epsilonByGroup), ...
                cfg.risk.barEpsilon, AbsTol=1e-12);
        end

        function modeProbabilityDoesNotChangeGroupAllowance(testCase)
            cfg = cca.defaults();
            firstEvents = localEvents(cfg, 2);
            secondEvents = firstEvents;
            firstEvents.probability = repmat([0.8; 0.2], ...
                cfg.timing.horizonSteps, 1);
            secondEvents.probability = repmat([0.55; 0.45], ...
                cfg.timing.horizonSteps, 1);
            first = cca.Risk.allocate( ...
                "CCA_FIXED_BUDGET", firstEvents, cfg);
            second = cca.Risk.allocate( ...
                "CCA_FIXED_BUDGET", secondEvents, cfg);
            testCase.verifyEqual(first.epsilonByGroup, ...
                second.epsilonByGroup, AbsTol=1e-14);
            rows = reshape(first.conditionalEpsilon, 2, [])';
            testCase.verifyEqual(rows(:, 1), rows(:, 2), AbsTol=0);
        end

        function omittedModeMassIsRejected(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 2);
            events.omittedMassByGroup(1) = 1e-3;
            testCase.verifyError( ...
                @() cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg), ...
                "cca:risk:OmittedMass");
        end

        function omittedMassShapeIsRejected(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 2);
            events.omittedMassByGroup = 0;
            testCase.verifyError( ...
                @() cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg), ...
                "cca:risk:OmittedMassShape");
        end

        function invalidDomainIsRejected(testCase)
            cfg = cca.defaults();
            cfg.risk.epsilonMin = ...
                cfg.risk.barEpsilon / cfg.timing.horizonSteps;
            testCase.verifyError( ...
                @() cca.Risk.allocate( ...
                    "CCA_FIXED_BUDGET", localEvents(cfg, 2), cfg), ...
                "cca:risk:Domain");
        end

        function modeVaryingContextIsRejected(testCase)
            cfg = cca.defaults();
            events = localEvents(cfg, 2);
            events.context(2) = events.context(2) + 0.01;
            testCase.verifyError( ...
                @() cca.Risk.allocate("CCA_FIXED_BUDGET", events, cfg), ...
                "cca:risk:ModeContext");
        end
    end
end

function events = localEvents(cfg, modeCount)
N = cfg.timing.horizonSteps;
events.humanIndex = ones(N * modeCount, 1);
events.stageIndex = repelem((1:N)', modeCount);
events.modeIndex = repmat((1:modeCount)', N, 1);
events.probability = repmat(ones(modeCount, 1) / modeCount, N, 1);
events.context = repelem(linspace(0, 1, N)', modeCount);
events.omittedMassByGroup = zeros(1, N);
end

function output = localPermute(events, permutation)
output = events;
fields = ["humanIndex", "stageIndex", "modeIndex", ...
    "probability", "context"];
for field = fields
    output.(field) = events.(field)(permutation);
end
end

function events = localContextEvents(cfg, contextByGroup, modeCount)
groupCount = numel(contextByGroup);
assert(groupCount <= cfg.timing.horizonSteps);
events.humanIndex = ones(groupCount * modeCount, 1);
events.stageIndex = repelem((1:groupCount)', modeCount);
events.modeIndex = repmat((1:modeCount)', groupCount, 1);
events.probability = repmat(ones(modeCount, 1) / modeCount, ...
    groupCount, 1);
events.context = repelem(contextByGroup(:), modeCount);
events.omittedMassByGroup = zeros(1, groupCount);
end
