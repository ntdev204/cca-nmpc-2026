classdef Scenario
    methods (Static)
        function scenario = crossing()
        %CROSSING Two static context observations with directional uncertainty.
        
        scenario.name = "crossing_two_humans";
        scenario.target = [4; 0; 0; 0; 0; 0];
        scenario.contextPositionM = [2.0, 3.0; -1.2, 1.8];
        scenario.contextVelocityMps = [0.0, -0.10; 0.50, 0.00];
        scenario.humanYawRad = [0, 0];
        scenario.modeVelocityMps(:, :, 1) = [0.0, 0.0; 0.50, 0.30];
        scenario.modeVelocityMps(:, :, 2) = [-0.10, 0.0; 0.00, 0.00];
        scenario.modeProbability = [0.70, 0.30];
        scenario.basePredictionStdM = 0.08;
        scenario.stdGrowthMPerS = 0.04;
        end

        function scenario = literatureFamily(family, humanCount, seed)
        %LITERATUREFAMILY Seeded multi-human scenes derived from citations 03/04/05/07.
        
        arguments
            family (1, 1) string
            humanCount (1, 1) double {mustBeInteger, mustBePositive} = 3
            seed (1, 1) double {mustBeInteger, mustBeNonnegative} = 1
        end
        assert(humanCount >= 3, "cca:scenario:HumanCount", ...
            "Literature-driven scenes require at least three humans.");
        
        stream = RandStream("mt19937ar", Seed=seed);
        family = lower(family);
        switch family
            case "circular"
                scenario = localCircular(stream, humanCount);
                scenario.family = "circular_convergence";
            case "random"
                scenario = localRandom(stream, humanCount);
                scenario.family = "random_crossing";
            case "parallel"
                scenario = localParallel(stream, humanCount);
                scenario.family = "parallel_counterflow";
            case "multimodal"
                scenario = localMultimodal(stream, humanCount);
                scenario.family = "multimodal_non_yielding";
            otherwise
                error("cca:scenario:Family", ...
                    "Unknown literature-driven scenario family %s.", family);
        end
        
        scenario.name = sprintf("%s_h%d_seed%d", ...
            scenario.family, humanCount, seed);
        scenario.seed = seed;
        scenario.target = [4.2; 0; 0; 0; 0; 0];
        scenario.durationS = 5.0;
        scenario.basePredictionStdM = 0.07;
        scenario.stdGrowthMPerS = 0.05;
        scenario.humanYawRad = atan2( ...
            scenario.contextVelocityMps(2, :), ...
            scenario.contextVelocityMps(1, :));
        function scenario = localCircular(stream, count)
        center = [2.15; 0.0];
        angles = linspace(-0.55 * pi, 1.45 * pi, count + 1);
        angles(end) = [];
        angles = angles + 0.10 * (rand(stream, 1, count) - 0.5);
        speed = 0.42 + 0.10 * rand(stream, 1, count);
        arrival = 2.6 + 0.5 * rand(stream, 1, count);
        velocity = [cos(angles); sin(angles)] .* speed;
        
        scenario.contextVelocityMps = velocity;
        scenario.contextPositionM = center - velocity .* arrival;
        scenario.modeVelocityMps = localTwoModes(velocity);
        scenario.modeProbability = repmat([0.72; 0.28], 1, count);
        end
        
        function scenario = localRandom(stream, count)
        crossingX = linspace(1.45, 3.15, count) + ...
            0.18 * (rand(stream, 1, count) - 0.5);
        arrival = linspace(2.0, 3.8, count) + ...
            0.25 * (rand(stream, 1, count) - 0.5);
        direction = (-1) .^ (1:count);
        speed = 0.38 + 0.16 * rand(stream, 1, count);
        velocity = [0.08 * (rand(stream, 1, count) - 0.5); ...
            direction .* speed];
        interactionY = 0.18 * (rand(stream, 1, count) - 0.5);
        interaction = [crossingX; interactionY];
        
        scenario.contextVelocityMps = velocity;
        scenario.contextPositionM = interaction - velocity .* arrival;
        scenario.modeVelocityMps = localTwoModes(velocity);
        scenario.modeProbability = repmat([0.68; 0.32], 1, count);
        end
        
        function scenario = localParallel(stream, count)
        lanes = linspace(-0.72, 0.72, count);
        lanes(ceil(count / 2)) = 0.02;
        velocity = zeros(2, count);
        initial = zeros(2, count);
        for human = 1:count
            if mod(human, 2) == 1
                velocity(:, human) = [-0.34 - 0.06 * rand(stream); 0];
                initial(:, human) = [3.1 + 0.35 * rand(stream); lanes(human)];
            else
                velocity(:, human) = [0.24 + 0.06 * rand(stream); 0];
                initial(:, human) = [0.7 + 0.35 * rand(stream); lanes(human)];
            end
        end
        critical = ceil(count / 2);
        velocity(:, critical) = [-0.42; 0];
        initial(:, critical) = [3.05; 0.02];
        
        scenario.contextVelocityMps = velocity;
        scenario.contextPositionM = initial;
        scenario.modeVelocityMps = localTwoModes(velocity);
        scenario.modeProbability = repmat([0.75; 0.25], 1, count);
        end
        
        function scenario = localMultimodal(stream, count)
        base = localRandom(stream, count);
        critical = ceil(count / 2);
        base.contextPositionM(:, critical) = [2.05; -1.05];
        base.contextVelocityMps(:, critical) = [0; 0.18];
        
        base.modeVelocityMps = localTwoModes(base.contextVelocityMps);
        base.modeVelocityMps(:, 1, critical) = [0; 0.18];
        base.modeVelocityMps(:, 2, critical) = [0; 0.62];
        base.modeProbability = repmat([0.72; 0.28], 1, count);
        scenario = base;
        end
        
        function modes = localTwoModes(velocity)
        count = size(velocity, 2);
        modes = zeros(2, 2, count);
        rotation = [cos(pi / 12), -sin(pi / 12); ...
                    sin(pi / 12),  cos(pi / 12)];
        for human = 1:count
            modes(:, 1, human) = velocity(:, human);
            signAngle = 1 - 2 * mod(human, 2);
            if signAngle < 0
                lateralRotation = rotation';
            else
                lateralRotation = rotation;
            end
            modes(:, 2, human) = ...
                0.72 * lateralRotation * velocity(:, human);
        end
        end
        
        end

        function safety = predict(scenario, timeS, nominalStates, cfg, ...
            robotPositionCovarianceM2, humanRobotCrossCovarianceM2)
        %PREDICT Build complete multimodal events on one frozen nominal trajectory.
        
        N = cfg.timing.horizonSteps;
        humanCount = size(scenario.contextPositionM, 2);
        modeCount = size(scenario.modeVelocityMps, 2);
        eventCount = humanCount * N * modeCount;
        events.humanIndex = zeros(eventCount, 1);
        events.stageIndex = zeros(eventCount, 1);
        events.modeIndex = zeros(eventCount, 1);
        events.probability = zeros(eventCount, 1);
        events.context = zeros(eventCount, 1);
        events.omittedMassByGroup = zeros(humanCount, N);
        meanPosition = zeros(2, eventCount);
        meanVelocity = zeros(2, eventCount);
        humanCovariance = zeros(2, 2, eventCount);
        relativeCovariance = zeros(2, 2, eventCount);
        separatingDirection = zeros(2, eventCount);
        assert(isequal(size(robotPositionCovarianceM2), [2, 2, N]), ...
            "cca:scenario:RobotCovariance", ...
            "Robot covariance must have shape [2,2,stage].");
        assert(isequal(size(humanRobotCrossCovarianceM2), ...
            [2, 2, humanCount, modeCount, N]), ...
            "cca:scenario:CrossCovariance", ...
            "Cross covariance must have shape [2,2,human,mode,stage].");
        assert(all(isfinite(robotPositionCovarianceM2), "all") && ...
            all(isfinite(humanRobotCrossCovarianceM2), "all"));
        
        current = scenario.contextPositionM;
        index = 0;
        for human = 1:humanCount
            for stage = 1:N
                horizonTime = stage * cfg.timing.sampleTimeS;
                sigma = scenario.basePredictionStdM + ...
                    scenario.stdGrowthMPerS * horizonTime;
                for mode = 1:modeCount
                    index = index + 1;
                    probability = localModeProbability( ...
                        scenario, mode, human, modeCount, humanCount);
                    [position, velocity] = localModeState( ...
                        scenario, current(:, human), mode, human);
                    events.humanIndex(index) = human;
                    events.stageIndex(index) = stage;
                    events.modeIndex(index) = mode;
                    events.probability(index) = probability;
                    meanPosition(:, index) = position;
                    meanVelocity(:, index) = velocity;
                    humanCovariance(:, :, index) = sigma^2 * eye(2);
                    cross = humanRobotCrossCovarianceM2(:, :, human, mode, stage);
                    relative = humanCovariance(:, :, index) + ...
                        robotPositionCovarianceM2(:, :, stage) - cross - cross';
                    relative = 0.5 * (relative + relative');
                    assert(min(eig(relative)) >= -1e-10, ...
                        "cca:scenario:RelativeCovariance", ...
                        "Relative covariance must be positive semidefinite.");
                    relativeCovariance(:, :, index) = relative;
                    difference = nominalStates(1:2, stage + 1) - position;
                    distance = norm(difference);
                    if distance < cfg.safety.minimumNormalDistanceM
                        separatingDirection(:, index) = [1; 0];
                    else
                        separatingDirection(:, index) = difference / distance;
                    end
                end
            end
        end
        events.context = cca.score( ...
            nominalStates, events, meanPosition, meanVelocity, cfg);
        events.context = localGroupContext(events);
        events.context = localContextMode(events, cfg);
        
        safety.active = true;
        safety.events = events;
        safety.meanPositionM = meanPosition;
        safety.meanVelocityMps = meanVelocity;
        safety.relativeCovarianceM2 = relativeCovariance;
        safety.separatingDirection = separatingDirection;
        safety.nominalRobotPositionM = nominalStates(1:2, 2:end);
        safety.humanYawRad = atan2(meanVelocity(2, :), ...
            meanVelocity(1, :))';
        function context = localGroupContext(events)
        % Context belongs to e=(human,stage), never to an individual LSTM mode.
        
        context = events.context;
        keys = unique([events.humanIndex(:), events.stageIndex(:)], ...
            "rows", "sorted");
        for index = 1:size(keys, 1)
            group = events.humanIndex == keys(index, 1) & ...
                events.stageIndex == keys(index, 2);
            context(group) = max(context(group));
        end
        end
        
        function probability = localModeProbability( ...
                scenario, mode, human, modeCount, humanCount)
        probability = scenario.modeProbability;
        if isvector(probability)
            probability = probability(:);
            assert(numel(probability) == modeCount);
            probability = probability(mode);
        else
            assert(isequal(size(probability), [modeCount, humanCount]));
            probability = probability(mode, human);
        end
        end
        
        function [position, velocity] = localModeState( ...
                scenario, current, mode, human)
        position = current;
        velocity = scenario.modeVelocityMps(:, mode, human);
        end
        
        function context = localContextMode(events, cfg)
        context = events.context;
        mode = upper(string(cfg.context.mode));
        switch mode
            case "NOMINAL"
                return;
            case "CONSTANT"
                context(:) = 0.5;
            case "PERMUTED"
                humanCount = max(events.humanIndex);
                for stage = 1:cfg.timing.horizonSteps
                    values = zeros(humanCount, 1);
                    for human = 1:humanCount
                        group = events.humanIndex == human & ...
                            events.stageIndex == stage;
                        values(human) = context(find(group, 1, "first"));
                    end
                    values = flipud(values);
                    for human = 1:humanCount
                        group = events.humanIndex == human & ...
                            events.stageIndex == stage;
                        context(group) = values(human);
                    end
                end
            otherwise
                error("cca:context:Mode", "Unknown context mode %s.", mode);
        end
        end
        
        end
    end
end
