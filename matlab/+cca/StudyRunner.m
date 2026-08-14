classdef StudyRunner
    methods (Static)
        function study = runContextAblation(cfg)
        %RUNCONTEXTABLATION Nominal, constant and permuted context mechanism test.
        
        contextModes = ["nominal", "constant", "permuted"];
        controllers = "CCA_FIXED_BUDGET";
        rows = cell(numel(contextModes) * numel(controllers), 1);
        results = cell(size(rows));
        scenario = cca.Scenario.crossing();
        index = 0;
        for mode = contextModes
            local = cfg;
            local.context.mode = mode;
            for controller = controllers
                index = index + 1;
                results{index} = cca.Simulation.simulateScenario( ...
                    controller, scenario, local);
                row = cca.StudyMetrics.summarizeScenario(results{index}, local);
                row.ContextMode = mode;
                rows{index} = row;
            end
        end
        study.summary = vertcat(rows{:});
        study.results = results;
        end

        function study = runFoundation(cfg, includeNmpc)
        %RUNFOUNDATION Open-loop structure and matched regulation comparisons.
        
        open = cca.AnalysisTools.openLoop(cfg);
        study.openLoop = table( ...
            open.continuousControllabilityRank, open.controllabilityRank, ...
            open.inputRank, open.inputNullity, ...
            min(open.effectiveInertiaEigenvalues), ...
            max(real(open.continuousPoles)), max(abs(open.discretePoles)), ...
            open.zohStateMatrixError, open.zohInputMatrixError, ...
            open.zohParityPass, ...
            open.nullspaceResidual, ...
            open.equilibriumResidual, open.powerDualityResidual, ...
            open.minimumInputSingularValue, ...
            VariableNames=["ContinuousControllabilityRank", ...
            "DiscreteControllabilityRank", "InputRank", "InputNullity", ...
            "MinimumInertiaEigenvalue", "MaximumContinuousPoleRealPart", ...
            "MaximumOpenLoopPoleMagnitude", "ZohStateMatrixError", ...
            "ZohInputMatrixError", "ZohParityPass", ...
            "NullspaceResidual", "EquilibriumResidual", ...
            "PowerDualityResidual", "MinimumInputSingularValue"]);
        
        certificate = cca.AnalysisTools.stability(cfg);
        study.stability = struct2table(certificate, AsArray=true);
        study.openLoopChannels = cca.AnalysisTools.openLoopChannels(cfg);
        study.openLoopPulseChannels = cca.AnalysisTools.openLoopPulseChannels(cfg);
        study.overActuation = cca.AnalysisTools.overActuation(cfg);
        study.feedbackNecessity = cca.AnalysisTools.feedbackNecessity(cfg);
        study.regionOfAttraction = struct2table( ...
            cca.AnalysisTools.regionOfAttraction(cfg), AsArray=true);
        parity = cca.AnalysisTools.numericalParity(cfg);
        study.numericalParity = struct2table(parity, AsArray=true);
        discrepancy = cca.AnalysisTools.modelDiscrepancy(cfg);
        study.modelDiscrepancy = table(discrepancy.oneStepStateError, ...
            discrepancy.horizonStateError, discrepancy.maximumPositionErrorM, ...
            discrepancy.maximumVelocityError, ...
            VariableNames=["OneStepStateError", "HorizonStateError", ...
            "MaximumPositionErrorM", "MaximumVelocityError"]);
        
        scenarios = localScenarios();
        controllers = ["OPEN_LOOP", "PID", "LQR"];
        if includeNmpc
            controllers(end + 1) = "NMPC";
            study.localNmpcStability = struct2table( ...
                cca.AnalysisTools.localNmpcStability(cfg), AsArray=true);
        end
        rows = cell(numel(scenarios) * numel(controllers), 1);
        responseResults = cell(size(rows));
        index = 0;
        for s = 1:numel(scenarios)
            for c = 1:numel(controllers)
                index = index + 1;
                responseResults{index} = cca.Simulation.simulate( ...
                    controllers(c), scenarios(s).target, cfg);
                rows{index} = cca.StudyMetrics.summarizeResponse( ...
                    responseResults{index}, scenarios(s), cfg);
            end
        end
        study.response = vertcat(rows{:});
        study.responseResults = responseResults;
        study.config = cfg;
        function scenarios = localScenarios()
        scenarios(1) = localScenario("x", [1; 0; 0; 0; 0; 0], [1; 0; 0]);
        scenarios(2) = localScenario("y", [0; 1; 0; 0; 0; 0], [0; 1; 0]);
        scenarios(3) = localScenario( ...
            "diagonal", [1; 1; 0; 0; 0; 0], [1; 1; 0] / sqrt(2));
        scenarios(4) = localScenario( ...
            "yaw", [0; 0; pi / 2; 0; 0; 0], [0; 0; 1]);
        end
        
        function scenario = localScenario(name, target, projection)
        scenario.name = name;
        scenario.target = target;
        scenario.projection = projection;
        end
        
        end

        function study = runRobustness(cfg, envelope)
        
        if nargin < 2
            envelope = "development";
        end
        scenario.name = "diagonal";
        scenario.target = [1; 1; 0; 0; 0; 0];
        scenario.projection = [1; 1; 0] / sqrt(2);
        controllers = ["LQR", "NMPC"];
        switch upper(string(envelope))
            case {"DEVELOPMENT", "VALIDATION", "CONFIRMATION"}
                cases = cca.StudyMetrics.physicalCases(envelope);
            otherwise
                error("cca:study:Envelope", "Unknown envelope %s.", envelope);
        end
        rows = cell(numel(controllers) * numel(cases), 1);
        results = cell(size(rows));
        index = 0;
        
        for i = 1:numel(cases)
            local = cfg;
            item = cases(i);
            local.study.plantMode = item.PlantMode;
            local.study.constantDisturbance = item.Disturbance;
            local.plant.massScale = item.MassScale;
            local.plant.yawInertiaScale = item.YawInertiaScale;
            local.plant.viscousDampingScale = item.ViscousDampingScale;
            local.plant.coulombFrictionScale = item.CoulombFrictionScale;
            local.plant.actuatorTimeConstantS = item.ActuatorLagS;
            local.plant.commandDelayS = item.CommandDelayS;
            for controller = controllers
                index = index + 1;
                results{index} = cca.Simulation.simulate( ...
                    controller, scenario.target, local);
                row = cca.StudyMetrics.summarizeResponse( ...
                    results{index}, scenario, local);
                row.PlantCase = item.Name;
                row.PlantMode = item.PlantMode;
                row.MassScale = item.MassScale;
                row.YawInertiaScale = item.YawInertiaScale;
                row.ViscousDampingScale = item.ViscousDampingScale;
                row.CoulombFrictionScale = item.CoulombFrictionScale;
                row.ActuatorLagS = item.ActuatorLagS;
                row.CommandDelayS = item.CommandDelayS;
                row.DisturbanceNorm = norm(local.study.constantDisturbance);
                rows{index} = row;
            end
        end
        
        study.summary = vertcat(rows{:});
        study.results = results;
        study.envelope = string(envelope);
        end

        function study = runPositionState(cfg)
        scenarios = struct( ...
            "Name", {"x", "y", "diagonal", "yaw"}, ...
            "Target", {[1; 0; 0; 0; 0; 0], [0; 1; 0; 0; 0; 0], ...
            [1; 1; 0; 0; 0; 0], [0; 0; pi / 2; 0; 0; 0]});
        controllers = ["MPC", "NMPC", "DWA", "MPPI", "CCA_NMPC"];
        rows = cell(numel(scenarios) * numel(controllers), 1);
        results = cell(size(rows));
        index = 0;
        for s = 1:numel(scenarios)
            for c = 1:numel(controllers)
                index = index + 1;
                result = cca.Simulation.simulatePosition( ...
                    controllers(c), scenarios(s).Target, cfg);
                results{index} = result;
                rows{index} = table(controllers(c), string(scenarios(s).Name), ...
                    result.finalPositionErrorM, result.positionRmseM, ...
                    result.yawRmseRad, result.meanCommandVariationNorm, ...
                    VariableNames=["Controller", "Scenario", ...
                    "FinalPositionErrorM", "PositionRmseM", ...
                    "YawRmseRad", "MeanCommandVariationNorm"]);
            end
        end
        study.summary = vertcat(rows{:});
        study.results = results;
        study.controlMode = "position_state";
        study.stateDefinition = ["x", "y", "theta", "vx", "vy", "omega"];
        study.commandDefinition = ["vx_cmd", "vy_cmd", "wz_cmd"];
        end

        function study = runStochastic(cfg)
        %RUNSTOCHASTIC Matched deterministic and risk-allocation crossing comparison.
        
        scenario = cca.Scenario.crossing();
        controllers = [ ...
            "DETERMINISTIC", ...
            "UNIFORM", ...
            "CCA_FIXED_BUDGET" ...
        ];
        results = cell(numel(controllers), 1);
        rows = cell(numel(controllers), 1);
        for i = 1:numel(controllers)
            results{i} = cca.Simulation.simulateScenario( ...
                controllers(i), scenario, cfg);
            rows{i} = cca.StudyMetrics.summarizeScenario(results{i}, cfg);
        end
        study.scenario = scenario;
        study.results = results;
        study.summary = vertcat(rows{:});
        end

        function study = runTrajectoryTracking(cfg)
        %RUNTRAJECTORYTRACKING Matched LQR/NMPC figure-eight tracking study.
        
        controllers = ["LQR", "NMPC"];
        study.results = cell(numel(controllers), 1);
        rows = cell(numel(controllers), 1);
        for i = 1:numel(controllers)
            study.results{i} = cca.Simulation.simulateTrajectory(controllers(i), cfg);
            rows{i} = cca.StudyMetrics.summarizeTrajectory(study.results{i}, cfg);
        end
        study.summary = vertcat(rows{:});
        study.referenceKind = "figure_eight";
        end
    end
end
