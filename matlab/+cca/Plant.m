classdef Plant
    methods (Static)
        function [nextState, nextPlant] = advance(state, command, ...
            previousCommand, plantState, cfg)
        %ADVANCE Select nominal controller model or independent mismatched plant.
        
        mode = upper(string(cfg.study.plantMode));
        switch mode
            case "NOMINAL"
                nextState = cca.Model.rk4(state, command, ...
                    cfg.study.constantDisturbance, cfg.timing.sampleTimeS, cfg.robot);
                nextPlant = [];
            case "MISMATCHED"
                if isempty(plantState)
                    plantState = [state; zeros(4, 1)];
                else
                    plantState(1:6) = state;
                end
                nextPlant = cca.Plant.step(plantState, command, previousCommand, ...
                    cfg.study.constantDisturbance, cfg);
                nextState = nextPlant(1:6);
            otherwise
                error("cca:plant:Mode", "Unknown plant mode %s.", mode);
        end
        end

        function robot = robotParameters(cfg)
        %ROBOTPARAMETERS Deliberately mismatched simulation plant parameters.
        
        robot = cfg.robot;
        robot.massKg = cfg.plant.massScale * robot.massKg;
        robot.yawInertiaKgm2 = ...
            cfg.plant.yawInertiaScale * robot.yawInertiaKgm2;
        robot.viscousDamping = ...
            cfg.plant.viscousDampingScale * robot.viscousDamping;
        robot.coulombFriction = ...
            cfg.plant.coulombFrictionScale * robot.coulombFriction;
        end

        function states = rollout(x0, commands, disturbance, cfg)
        %ROLLOUT Propagate the independent lagged plant for a command sequence.
        
        count = size(commands, 2);
        states = zeros(10, count + 1);
        states(1:6, 1) = x0;
        previous = zeros(4, 1);
        for k = 1:count
            states(:, k + 1) = cca.Plant.step( ...
                states(:, k), commands(:, k), previous, disturbance, cfg);
            previous = commands(:, k);
        end
        end

        function next = step(plantState, command, previousCommand, ...
            disturbance, cfg)
        %STEP Fine-step actuator-lag and parameter-mismatch plant.
        
        arguments
            plantState (10, 1) double {mustBeFinite}
            command (4, 1) double {mustBeFinite}
            previousCommand (4, 1) double {mustBeFinite}
            disturbance (3, 1) double {mustBeFinite}
            cfg struct
        end
        
        robot = cca.Plant.robotParameters(cfg);
        substeps = cfg.plant.integrationSubsteps;
        dt = cfg.timing.sampleTimeS / substeps;
        state = plantState(1:6);
        applied = plantState(7:10);
        for substep = 1:substeps
            elapsed = (substep - 0.5) * dt;
            if elapsed <= cfg.plant.commandDelayS
                delayed = previousCommand;
            else
                delayed = command;
            end
            derivative = (delayed - applied) / ...
                cfg.plant.actuatorTimeConstantS;
            applied = applied + dt * derivative;
            applied = min(cfg.actuator.torqueMaxNm, ...
                max(cfg.actuator.torqueMinNm, applied));
            state = cca.Model.rk4(state, applied, disturbance, dt, robot);
        end
        next = [state; applied];
        end
    end
end

