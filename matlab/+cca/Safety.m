classdef Safety
    methods (Static)
        function acceleration = brakingAcceleration(normalWorld, state, cfg)
        %BRAKINGACCELERATION Torque-feasible separation acceleration for one normal.
        
        psi = state(3);
        worldFromBody = [cos(psi), -sin(psi); sin(psi), cos(psi)];
        normalBody = worldFromBody' * normalWorld(:);
        model = cca.Model.matrices(cfg.robot);
        translationMap = model.effectiveInertia(1:2, 1:2) \ ...
            model.bodyWrenchMap(1:2, :);
        coefficient = normalBody' * translationMap;
        lower = cfg.actuator.torqueMinNm(:)';
        upper = cfg.actuator.torqueMaxNm(:)';
        maximum = sum(max(coefficient .* lower, coefficient .* upper));
        usable = cfg.safety.actuatorAuthorityFraction * maximum - ...
            cfg.safety.residualAccelerationBoundMps2;
        acceleration = max(usable, 1e-3);
        end

        function support = ellipseSupport(normalWorld, semiaxes, yaw)
        %ELLIPSESUPPORT Support of a rotated human ellipse along a world normal.
        
        rotation = [cos(yaw), -sin(yaw); sin(yaw), cos(yaw)];
        shape = rotation * diag(semiaxes(:) .^ 2) * rotation';
        support = sqrt(max(0, normalWorld' * shape * normalWorld));
        end
    end
end

