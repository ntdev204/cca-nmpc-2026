function results = run_studies(options)
%RUN_STUDIES Run in-memory MATLAB proof studies without creating artifacts.

arguments
    options.IncludeNmpc (1, 1) logical = true
    options.IncludeStochastic (1, 1) logical = true
    options.IncludeRobustness (1, 1) logical = true
    options.IncludeContextAblation (1, 1) logical = true
    options.IncludeTrajectoryTracking (1, 1) logical = true
    options.IncludePositionState (1, 1) logical = true
    options.IncludeCompatibilityStudies (1, 1) logical = false
    options.ExportResults (1, 1) logical = false
    options.Profile (1, 1) string = "full"
    options.OutputDirectory (1, 1) string = ""
end

setup_project();
cfg = cca.defaults();
profile = lower(options.Profile);
switch profile
    case "full"
    case "bounded"
        cfg.study.durationS = 0.25;
        cfg.study.trajectoryDurationS = 0.50;
        cfg.solver.maxIterations = 16;
        cfg.solver.maxFunctionEvaluations = 3000;
        cfg.solver.optimalityTolerance = 1e-3;
        cfg.solver.stepTolerance = 1e-6;
    otherwise
        error("cca:study:Profile", "Unknown run profile %s.", profile);
end
cfg.study.profile = profile;
if options.IncludePositionState
    results.positionState = cca.StudyRunner.runPositionState(cfg);
end
if options.IncludeCompatibilityStudies
    results.foundationCompatibility = cca.StudyRunner.runFoundation( ...
        cfg, options.IncludeNmpc);
    if options.IncludeStochastic
        results.stochastic = cca.StudyRunner.runStochastic(cfg);
    end
    if options.IncludeRobustness
        results.robustnessDevelopment = ...
            cca.StudyRunner.runRobustness(cfg, "development");
        results.robustnessConfirmation = ...
            cca.StudyRunner.runRobustness(cfg, "confirmation");
    end
    if options.IncludeContextAblation
        results.contextAblation = cca.StudyRunner.runContextAblation(cfg);
    end
    if options.IncludeTrajectoryTracking
        results.trajectoryTracking = cca.StudyRunner.runTrajectoryTracking(cfg);
    end
end
if isfield(results, "foundationCompatibility")
    foundation = results.foundationCompatibility;
    disp(foundation.openLoop);
    disp(foundation.openLoopChannels);
    disp(foundation.openLoopPulseChannels);
    disp(foundation.overActuation);
    disp(foundation.feedbackNecessity.summary);
    disp(foundation.stability);
    disp(foundation.regionOfAttraction);
    if isfield(foundation, "localNmpcStability")
        disp(foundation.localNmpcStability);
    end
    disp(foundation.numericalParity);
    disp(foundation.modelDiscrepancy);
    disp(foundation.response);
end
if isfield(results, "positionState")
    disp(results.positionState.summary);
end
if isfield(results, "stochastic")
    disp(results.stochastic.summary);
end
if isfield(results, "robustnessDevelopment")
    disp(results.robustnessDevelopment.summary);
    disp(results.robustnessConfirmation.summary);
end
if isfield(results, "contextAblation")
    disp(results.contextAblation.summary);
end
if isfield(results, "trajectoryTracking")
    disp(results.trajectoryTracking.summary);
end
if options.ExportResults
    output = options.OutputDirectory;
    if strlength(output) == 0
        sourceRoot = fileparts(mfilename("fullpath"));
        runName = "matlab_" + lower(profile) + "_" + ...
            string(datetime("now", "TimeZone", "UTC", ...
            "Format", "yyyyMMdd'T'HHmmss'Z'"));
        output = fullfile(sourceRoot, "..", "..", "experiments", "runs", runName);
    end
    if options.IncludeCompatibilityStudies
        cca.StudyIO.exportResults(results, cfg, output, RequireGate=profile == "full");
    else
        assert(isfield(results, "positionState"), ...
            "cca:study:PositionExport", ...
            "Position-state export requires IncludePositionState=true.");
        cca.StudyIO.exportPositionState(results.positionState, cfg, output);
    end
end
end
