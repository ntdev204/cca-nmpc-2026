classdef Risk
    methods (Static)
        function result = allocate(strategy, events, cfg)
        %ALLOCATE Canonical fixed-budget allocation over e=(human, stage).
        %
        % w_e = softmax(-beta*c_e)
        % epsilon_e = epsilonMin + (barEpsilon-M*epsilonMin)*w_e
        % result.softmaxClipped records use of the floating-point log-weight floor.
        
        strategy = upper(string(strategy));
        problem = cca.Risk.prepare(events, cfg);
        M = problem.groupCount;
        epsilonMin = cfg.risk.epsilonMin;
        barEpsilon = cfg.risk.barEpsilon;
        contextBeta = cfg.risk.contextBeta;
        assert(isfinite(epsilonMin) && epsilonMin >= 0 && ...
            isfinite(barEpsilon) && barEpsilon > 0 && barEpsilon < 0.5 && ...
            epsilonMin < barEpsilon / M && ...
            isfinite(contextBeta) && contextBeta >= 0, ...
            "cca:risk:Domain", ...
            "Require 0 <= epsilonMin < barEpsilon/M, 0 < barEpsilon < 0.5, beta >= 0.");
        
        switch strategy
            case "UNIFORM"
                beta = 0;
            case "CCA_FIXED_BUDGET"
                beta = contextBeta;
            otherwise
                error("cca:risk:Strategy", "Unknown strategy %s.", strategy);
        end
        
        logits = -beta * problem.groupContext;
        assert(all(isfinite(logits)), ...
            "cca:risk:LogitOverflow", ...
            "Risk logits must remain finite; reduce beta or reject the snapshot.");
        shifted = logits - max(logits);
        logWeightFloor = log(realmin);
        softmaxClipped = any(shifted < logWeightFloor);
        shifted = max(shifted, logWeightFloor);
        exponentials = exp(shifted);
        weights = exponentials / sum(exponentials);
        epsilonByGroup = epsilonMin + ...
            (barEpsilon - M * epsilonMin) * weights;
        conditionalEpsilon = epsilonByGroup(problem.groupIndex);
        assert(all(isfinite(weights)) && all(weights > 0));
        assert(all(epsilonByGroup >= epsilonMin & epsilonByGroup < 0.5));
        assert(abs(sum(epsilonByGroup) - barEpsilon) < 1e-12);
        
        result.strategy = strategy;
        result.groupHumanIndex = problem.groupHumanIndex;
        result.groupStageIndex = problem.groupStageIndex;
        result.weights = weights;
        result.epsilonByGroup = epsilonByGroup;
        result.conditionalEpsilon = conditionalEpsilon;
        result.epsilonTotal = barEpsilon;
        result.bound = barEpsilon;
        result.softmaxClipped = softmaxClipped;
        result.events = events;
        end

        function problem = prepare(events, cfg)
        %PREPARE Validate complete mode accounting for groups e=(human, stage).
        
        required = ["humanIndex", "stageIndex", "modeIndex", ...
            "probability", "context", "omittedMassByGroup"];
        for name = required
            assert(isfield(events, name), "cca:risk:MissingField", ...
                "Missing event field %s.", name);
        end
        
        human = events.humanIndex(:);
        stage = events.stageIndex(:);
        mode = events.modeIndex(:);
        probability = events.probability(:);
        context = events.context(:);
        count = numel(probability);
        assert(count > 0 && all([numel(human), numel(stage), ...
            numel(mode), numel(context)] == count), ...
            "cca:risk:Shape", "Risk rows must have one common nonzero length.");
        assert(all(isfinite(human) & human >= 1 & human == floor(human)));
        assert(all(isfinite(stage) & stage >= 1 & ...
            stage <= cfg.timing.horizonSteps & stage == floor(stage)));
        assert(all(isfinite(mode) & mode >= 1 & mode == floor(mode)));
        assert(all(isfinite(probability) & probability > 0));
        assert(all(isfinite(context) & context >= 0 & context <= 1));
        
        omitted = events.omittedMassByGroup;
        assert(all(isfinite(omitted), "all") && all(omitted == 0, "all"), ...
            "cca:risk:OmittedMass", ...
            "Omitted mode mass is prohibited for the confirmatory controller.");
        
        [groupKeys, ~, groupIndex] = unique([human, stage], "rows", "sorted");
        groupCount = size(groupKeys, 1);
        assert(numel(omitted) == groupCount, ...
            "cca:risk:OmittedMassShape", ...
            "Omitted mode mass needs one entry per human-stage group.");
        groupContext = zeros(groupCount, 1);
        for group = 1:groupCount
            rows = groupIndex == group;
            assert(numel(unique(mode(rows))) == nnz(rows), ...
                "cca:risk:DuplicateMode", ...
                "Mode IDs must be unique inside a human-stage group.");
            assert(abs(sum(probability(rows)) - 1) < 1e-10, ...
                "cca:risk:ProbabilityAccounting", ...
                "All retained mode probabilities must sum to one.");
            values = context(rows);
            assert(all(values == values(1)), "cca:risk:ModeContext", ...
                "Context must be group-level and mode invariant.");
            groupContext(group) = values(1);
        end
        
        problem.eventCount = count;
        problem.humanCount = numel(unique(human));
        problem.groupCount = groupCount;
        problem.groupHumanIndex = groupKeys(:, 1);
        problem.groupStageIndex = groupKeys(:, 2);
        problem.groupIndex = groupIndex;
        problem.groupContext = groupContext;
        problem.probability = probability;
        end
    end
end
