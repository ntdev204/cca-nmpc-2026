function context = score(nominalStates, events, meanPosition, ...
    meanVelocity, cfg)
%SCORE Monotone interaction-context proxy, separated from covariance.

count = numel(events.probability);
raw = zeros(count, 1);
humanCount = max(events.humanIndex);
density = min(1, max(0, humanCount - 1) / 3);

for i = 1:count
    stage = events.stageIndex(i);
    robot = nominalStates(:, stage + 1);
    robotVelocity = localWorldVelocity(robot);
    difference = robot(1:2) - meanPosition(:, i);
    distance = norm(difference);
    normal = difference / max(distance, 1e-6);
    relativeVelocity = robotVelocity - meanVelocity(:, i);
    closing = max(0, -normal' * relativeVelocity);
    cpaTime = max(0, -difference' * relativeVelocity / ...
        max(relativeVelocity' * relativeVelocity, 1e-6));
    crossing = localCrossing(robotVelocity, meanVelocity(:, i));
    features = [
        max(0, 1 - distance / cfg.context.distanceScaleM)
        min(1, closing / cfg.context.closingScaleMps)
        exp(-cpaTime / cfg.context.cpaTimeScaleS)
        crossing
        density
    ];
    argument = cfg.context.bias + cfg.context.weights' * features;
    raw(i) = 1 / (1 + exp(-argument));
end

context = zeros(count, 1);
for j = 1:humanCount
    for stage = 1:cfg.timing.horizonSteps
        group = events.humanIndex == j & events.stageIndex == stage;
        context(group) = max(raw(group));
    end
end
end

function velocity = localWorldVelocity(state)
psi = state(3);
velocity = [cos(psi), -sin(psi); ...
            sin(psi),  cos(psi)] * state(4:5);
end

function feature = localCrossing(robotVelocity, humanVelocity)
denominator = norm(robotVelocity) * norm(humanVelocity);
if denominator < 1e-6
    feature = 0;
else
    feature = abs(robotVelocity(1) * humanVelocity(2) - ...
        robotVelocity(2) * humanVelocity(1)) / denominator;
end
end
