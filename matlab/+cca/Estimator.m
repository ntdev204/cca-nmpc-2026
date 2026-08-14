classdef Estimator
    methods (Static)
        function filter = initialize(measurement, cfg)
        %INITIALIZE Initialize the six-state extended Kalman filter.
        
        arguments
            measurement (6, 1) double {mustBeFinite}
            cfg struct
        end
        
        filter.mean = measurement;
        filter.mean(3) = localWrap(filter.mean(3));
        filter.covariance = diag(cfg.estimator.initialStd(:) .^ 2);
        filter.covariance = localSymmetric(filter.covariance, ...
            cfg.estimator.covarianceFloor);
        function angle = localWrap(angle)
        angle = atan2(sin(angle), cos(angle));
        end
        
        function covariance = localSymmetric(covariance, floorValue)
        covariance = 0.5 * (covariance + covariance');
        [vectors, values] = eig(covariance);
        values = diag(max(diag(values), floorValue));
        covariance = vectors * values * vectors';
        covariance = 0.5 * (covariance + covariance');
        end
        
        end

        function noise = measurementNoise(sampleCount, cfg)
        %MEASUREMENTNOISE Reproducible matched sensor-noise sequence.
        
        arguments
            sampleCount (1, 1) double {mustBeInteger, mustBePositive}
            cfg struct
        end
        
        stream = RandStream("mt19937ar", ...
            Seed=cfg.estimator.measurementNoiseSeed);
        noise = cfg.estimator.measurementStd(:) .* ...
            randn(stream, 6, sampleCount);
        end

        function measurement = observe(trueState, noise)
        %OBSERVE Synthetic pose/body-velocity measurement with wrapped yaw.
        
        arguments
            trueState (6, 1) double {mustBeFinite}
            noise (6, 1) double {mustBeFinite}
        end
        
        measurement = trueState + noise;
        measurement(3) = atan2(sin(measurement(3)), cos(measurement(3)));
        end

        function filter = predict(filter, appliedTorque, cfg)
        %PREDICT EKF prediction through the same torque-input model used by NMPC.
        
        arguments
            filter struct
            appliedTorque (4, 1) double {mustBeFinite}
            cfg struct
        end
        
        prior = filter.mean;
        [stateJacobian, ~] = cca.Model.linearize( ...
            prior, appliedTorque, zeros(3, 1), cfg);
        filter.mean = cca.Model.rk4( ...
            prior, appliedTorque, zeros(3, 1), ...
            cfg.timing.sampleTimeS, cfg.robot);
        filter.mean(3) = localWrap(filter.mean(3));
        processCovariance = diag(cfg.estimator.processStdPerStep(:) .^ 2);
        filter.covariance = stateJacobian * filter.covariance * ...
            stateJacobian' + processCovariance;
        filter.covariance = localSymmetric(filter.covariance, ...
            cfg.estimator.covarianceFloor);
        function angle = localWrap(angle)
        angle = atan2(sin(angle), cos(angle));
        end
        
        function covariance = localSymmetric(covariance, floorValue)
        covariance = 0.5 * (covariance + covariance');
        [vectors, values] = eig(covariance);
        values = diag(max(diag(values), floorValue));
        covariance = vectors * values * vectors';
        covariance = 0.5 * (covariance + covariance');
        end
        
        end

        function filter = update(filter, measurement, cfg)
        %UPDATE Joseph-form EKF correction for pose and body-velocity measurements.
        
        arguments
            filter struct
            measurement (6, 1) double {mustBeFinite}
            cfg struct
        end
        
        measurementCovariance = diag(cfg.estimator.measurementStd(:) .^ 2);
        innovation = measurement - filter.mean;
        innovation(3) = localWrap(innovation(3));
        innovationCovariance = filter.covariance + measurementCovariance;
        gain = filter.covariance / innovationCovariance;
        filter.mean = filter.mean + gain * innovation;
        filter.mean(3) = localWrap(filter.mean(3));
        
        identity = eye(6);
        residual = identity - gain;
        filter.covariance = residual * filter.covariance * residual' + ...
            gain * measurementCovariance * gain';
        filter.covariance = localSymmetric(filter.covariance, ...
            cfg.estimator.covarianceFloor);
        function angle = localWrap(angle)
        angle = atan2(sin(angle), cos(angle));
        end
        
        function covariance = localSymmetric(covariance, floorValue)
        covariance = 0.5 * (covariance + covariance');
        [vectors, values] = eig(covariance);
        values = diag(max(diag(values), floorValue));
        covariance = vectors * values * vectors';
        covariance = 0.5 * (covariance + covariance');
        end
        
        end
    end
end

