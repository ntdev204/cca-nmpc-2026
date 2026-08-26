function states = rollout_states(initialState, commands, dt, velocityTimeConstant)
states = zeros(6, size(commands, 2) + 1);
states(:, 1) = initialState(:);
for k = 1:size(commands, 2)
    states(:, k + 1) = position_step( ...
        states(:, k), commands(:, k), dt, velocityTimeConstant);
end
end
