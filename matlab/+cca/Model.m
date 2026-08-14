classdef Model
    methods (Static)
        function dx = dynamics(x, torque, disturbance, robot)
        %DYNAMICS Legacy wheel-input dynamics retained for compatibility tests.
        
        arguments
            x (6, 1) double {mustBeFinite}
            torque (4, 1) double {mustBeFinite}
            disturbance (3, 1) double {mustBeFinite}
            robot struct
        end
        
        m = cca.Model.matrices(robot);
        nu = x(4:6);
        psi = x(3);
        rotation = [cos(psi), -sin(psi), 0; ...
                    sin(psi),  cos(psi), 0; ...
                    0,         0,        1];
        
        mx = m.effectiveInertia(1, 1);
        my = m.effectiveInertia(2, 2);
        vx = nu(1);
        vy = nu(2);
        omega = nu(3);
        coriolis = [-my * omega * vy; ...
                     mx * omega * vx; ...
                    (my - mx) * vx * vy];
        viscous = robot.viscousDamping(:) .* nu;
        coulomb = robot.coulombFriction(:) .* ...
            tanh(nu ./ robot.frictionSmoothing(:));
        acceleration = m.effectiveInertia \ ...
            (m.bodyWrenchMap * torque - coriolis - viscous - coulomb + disturbance);
        
        dx = [rotation * nu; acceleration];
        end

        function [A, B] = linearize(x, torque, disturbance, cfg)
        %LINEARIZE Central-difference linearization of the discrete RK4 model.
        
        nx = numel(x);
        nu = numel(torque);
        A = zeros(nx);
        B = zeros(nx, nu);
        stateStep = 1e-6 * max(1, abs(x));
        inputStep = 1e-6 * max(1, abs(torque));
        step = @(state, input) cca.Model.rk4(state, input, disturbance, ...
            cfg.timing.sampleTimeS, cfg.robot);
        
        for i = 1:nx
            delta = zeros(nx, 1);
            delta(i) = stateStep(i);
            A(:, i) = (step(x + delta, torque) - step(x - delta, torque)) ...
                / (2 * stateStep(i));
        end
        for i = 1:nu
            delta = zeros(nu, 1);
            delta(i) = inputStep(i);
            B(:, i) = (step(x, torque + delta) - step(x, torque - delta)) ...
                / (2 * inputStep(i));
        end
        end

        function [A, B] = linearizeContinuous(x, torque, disturbance, robot)
        %LINEARIZECONTINUOUS Central-difference Jacobian of continuous dynamics.
        
        nx = numel(x);
        nu = numel(torque);
        A = zeros(nx);
        B = zeros(nx, nu);
        stateStep = 1e-6 * max(1, abs(x));
        inputStep = 1e-6 * max(1, abs(torque));
        
        for i = 1:nx
            delta = zeros(nx, 1);
            delta(i) = stateStep(i);
            A(:, i) = ( ...
                cca.Model.dynamics(x + delta, torque, disturbance, robot) - ...
                cca.Model.dynamics(x - delta, torque, disturbance, robot)) ...
                / (2 * stateStep(i));
        end
        for i = 1:nu
            delta = zeros(nu, 1);
            delta(i) = inputStep(i);
            B(:, i) = ( ...
                cca.Model.dynamics(x, torque + delta, disturbance, robot) - ...
                cca.Model.dynamics(x, torque - delta, disturbance, robot)) ...
                / (2 * inputStep(i));
        end
        end

        function model = matrices(robot)
        %MATRICES Legacy Mecanum geometry and wheel-input compatibility map.
        
        r = robot.wheelRadiusM;
        L = robot.halfLengthM + robot.halfWidthM;
        A = [1, -1, -L; 1, 1, L; 1, 1, -L; 1, -1, L];
        bodyInertia = diag([robot.massKg, robot.massKg, robot.yawInertiaKgm2]);
        rotor = robot.wheelInertiaKgm2(:) + ...
            robot.gearRatio^2 * robot.motorInertiaKgm2(:);
        
        model.wheelKinematics = A / r;
        model.bodyWrenchMap = A' / r;
        model.bodyInertia = bodyInertia;
        model.effectiveInertia = bodyInertia + A' * diag(rotor) * A / r^2;
        model.leverArmM = L;
        model.inputRank = rank(model.bodyWrenchMap);
        model.inputNullspace = null(model.bodyWrenchMap);
        end

        function next = rk4(x, torque, disturbance, sampleTime, robot)
        %RK4 One zero-order-held fourth-order Runge-Kutta step.
        
        f = @(state) cca.Model.dynamics(state, torque, disturbance, robot);
        k1 = f(x);
        k2 = f(x + 0.5 * sampleTime * k1);
        k3 = f(x + 0.5 * sampleTime * k2);
        k4 = f(x + sampleTime * k3);
        next = x + sampleTime * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
        end

        function next = positionStep(x, command, sampleTime, velocityTimeConstant)
        arguments
            x (6, 1) double {mustBeFinite}
            command (3, 1) double {mustBeFinite}
            sampleTime (1, 1) double {mustBeFinite, mustBePositive}
            velocityTimeConstant (1, 1) double {mustBeFinite, mustBePositive}
        end

        blend = min(1, sampleTime / velocityTimeConstant);
        velocity = x(4:6) + blend * (command - x(4:6));
        psi = x(3);
        next = x;
        next(1:3) = x(1:3) + sampleTime * [ ...
            cos(psi) * velocity(1) - sin(psi) * velocity(2); ...
            sin(psi) * velocity(1) + cos(psi) * velocity(2); ...
            velocity(3)];
        next(4:6) = velocity;
        next(3) = atan2(sin(next(3)), cos(next(3)));
        end

        function states = rollout(x0, torques, disturbance, sampleTime, robot)
        %ROLLOUT Propagate a legacy wheel-input sequence for compatibility tests.
        
        horizon = size(torques, 2);
        states = zeros(6, horizon + 1);
        states(:, 1) = x0;
        for k = 1:horizon
            states(:, k + 1) = cca.Model.rk4( ...
                states(:, k), torques(:, k), disturbance, sampleTime, robot);
        end
        end
    end
end
