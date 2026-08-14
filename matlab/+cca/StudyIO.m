classdef StudyIO
    methods (Static)
        function artifacts = exportResults(results, cfg, output, options)
        arguments
            results struct
            cfg struct
            output
            options.RequireGate (1, 1) logical = true
        end
        %EXPORTRESULTS Write only the accepted, minimal Gate-A artifact set.
        
        required = ["stochastic", "contextAblation", ...
            "robustnessDevelopment", "robustnessConfirmation", ...
            "responseResults", "localNmpcStability", "trajectoryTracking"];
        assert(all(isfield(results, required)), ...
            "cca:study:FinalResults", "Final export requires every locked study.");
        gates = cca.StudyMetrics.buildAcceptanceTable(results);
        if options.RequireGate
            assert(gates.Pass(end), "cca:study:GateA", ...
                "Numerical Gate A failed; candidate artifacts were not exported.");
        end
        
        output = string(output);
        tableDirectory = fullfile(output, "tables");
        figureDirectory = fullfile(output, "figures");
        localPrepare(tableDirectory, "*.csv");
        localPrepare(figureDirectory, "*.png");
        manifestPath = fullfile(output, "manifest.json");
        if isfile(manifestPath)
            delete(manifestPath);
        end
        
        tableFiles = [
            localWrite(cca.StudyMetrics.buildCertificateTable(results), ...
                tableDirectory, "mathematical_certificates.csv")
            localWrite(results.response, tableDirectory, "control_response.csv")
            localWrite(cca.StudyMetrics.buildCcaComparisonTable(results), ...
                tableDirectory, "cca_comparison.csv")
            localWrite(results.robustnessDevelopment.summary, ...
                tableDirectory, "robustness_development.csv")
            localWrite(results.robustnessConfirmation.summary, ...
                tableDirectory, "robustness_confirmation.csv")
            localWrite(results.trajectoryTracking.summary, ...
                tableDirectory, "trajectory_tracking.csv")
            localWrite(gates, tableDirectory, "acceptance_gates.csv")
        ];
        figureFiles = cca.StudyIO.saveAllFigures(results, cfg, figureDirectory);
        artifacts = [tableFiles; figureFiles];
        manifest = cca.StudyIO.writeManifest( ...
            output, artifacts, cfg, gates, options.RequireGate);
        artifacts(end + 1) = manifest;
        function path = localWrite(input, directory, name)
        path = string(fullfile(directory, name));
        writetable(input, path);
        end
        
        function localPrepare(directory, pattern)
        if ~isfolder(directory)
            mkdir(directory);
        end
        files = dir(fullfile(directory, pattern));
        for i = 1:numel(files)
            delete(fullfile(files(i).folder, files(i).name));
        end
        end
        
        end

        function artifacts = exportPositionState(study, cfg, output)
        arguments
            study struct
            cfg struct
            output
        end
        assert(isfield(study, "summary") && isfield(study, "results"), ...
            "cca:study:PositionExport", "Position-state study is incomplete.");
        output = string(output);
        tableDirectory = fullfile(output, "tables");
        if ~isfolder(tableDirectory)
            mkdir(tableDirectory);
        end
        stale = dir(fullfile(tableDirectory, "position_state_*.csv"));
        for i = 1:numel(stale)
            delete(fullfile(stale(i).folder, stale(i).name));
        end
        artifacts = strings(0, 1);
        summaryPath = fullfile(tableDirectory, "position_state_summary.csv");
        writetable(study.summary, summaryPath);
        artifacts(end + 1) = string(summaryPath);
        for i = 1:numel(study.results)
            result = study.results{i};
            time = result.timeS(:);
            command = nan(numel(time), 3);
            command(1:(end - 1), :) = result.commands';
            data = table( ...
                time, result.states(1, :)', result.states(2, :)', ...
                result.states(3, :)', result.states(4, :)', ...
                result.states(5, :)', result.states(6, :)', ...
                command(:, 1), command(:, 2), command(:, 3), ...
                VariableNames=["t_s", "x_m", "y_m", "theta_rad", ...
                "vx_mps", "vy_mps", "omega_radps", "vx_cmd_mps", ...
                "vy_cmd_mps", "wz_cmd_radps"]);
            scenario = string(study.summary.Scenario(i));
            controller = string(result.controller);
            safeName = regexprep(lower(controller + "_" + scenario), ...
                "[^a-z0-9]+", "_");
            path = fullfile(tableDirectory, "position_state_" + safeName + ".csv");
            writetable(data, path);
            artifacts(end + 1) = string(path);
        end
        sourceRoot = string(fileparts(fileparts(mfilename("fullpath"))));
        sourceFiles = [dir(fullfile(sourceRoot, "+cca", "*.m")); ...
            dir(fullfile(sourceRoot, "run_studies.m")); ...
            dir(fullfile(sourceRoot, "setup_project.m"))];
        sourceTokens = strings(numel(sourceFiles), 1);
        for i = 1:numel(sourceFiles)
            path = fullfile(sourceFiles(i).folder, sourceFiles(i).name);
            sourceTokens(i) = replace(erase(string(path), sourceRoot + filesep), ...
                "\", "/") + ":" + localSha256File(path);
        end
        manifest.schema = "continuous-cca-nmpc-matlab-position-state-v1";
        manifest.generatedUtc = string(datetime("now", TimeZone="UTC", ...
            Format="yyyy-MM-dd'T'HH:mm:ss'Z'"));
        manifest.controlMode = "position_state";
        manifest.controlInterface = "body_velocity";
        manifest.stateDefinition = cellstr(study.stateDefinition);
        manifest.commandDefinition = cellstr(study.commandDefinition);
        manifest.controllers = cellstr(unique(study.summary.Controller, "stable"));
        manifest.scenarios = cellstr(unique(study.summary.Scenario, "stable"));
        if isfield(cfg.study, "profile")
            manifest.studyProfile = cfg.study.profile;
        else
            manifest.studyProfile = "unspecified";
        end
        manifest.configSha256 = localSha256Text(jsonencode(cfg));
        manifest.sourceSha256 = localSha256Text(strjoin(sort(sourceTokens), newline));
        manifest.evidenceStatus = "candidate-development-only";
        manifest.paperEdit = false;
        manifest.realTimeReady = false;
        manifest.hardwareValidated = false;
        manifest.assumptions = [ ...
            "synthetic offline MATLAB position-state simulation" ...
            "body-velocity commands only; no torque/current channel" ...
            "not a hardware or operational-safety result" ];
        names = strings(numel(artifacts), 1);
        hashes = strings(numel(artifacts), 1);
        outputNormalized = strip(replace(output, "\", "/"), "right", "/");
        for i = 1:numel(artifacts)
            normalized = replace(artifacts(i), "\", "/");
            names(i) = erase(normalized, outputNormalized + "/");
            hashes(i) = localSha256File(artifacts(i));
        end
        manifest.artifacts = struct("path", cellstr(names), ...
            "sha256", cellstr(hashes));
        manifestPath = fullfile(output, "manifest.json");
        if ~isfolder(output)
            mkdir(output);
        end
        file = fopen(manifestPath, "w");
        assert(file >= 0, "cca:study:Manifest", ...
            "Cannot open position-state manifest for writing.");
        cleanup = onCleanup(@() fclose(file));
        fprintf(file, "%s\n", jsonencode(manifest, PrettyPrint=true));
        clear cleanup
        artifacts(end + 1) = string(manifestPath);
        function digest = localSha256File(path)
        engine = java.security.MessageDigest.getInstance("SHA-256");
        file = fopen(path, "r");
        assert(file >= 0, "cca:study:Hash", "Cannot open file for hashing.");
        cleanup = onCleanup(@() fclose(file));
        while ~feof(file)
            bytes = fread(file, 8192, "*uint8");
            if ~isempty(bytes)
                chunk = typecast(bytes(:), "int8");
                engine.update(chunk, 0, numel(chunk));
            end
        end
        raw = typecast(engine.digest(), "uint8");
        digest = lower(string(reshape(dec2hex(raw, 2)', 1, [])));
        clear cleanup
        end
        function digest = localSha256Text(text)
        engine = java.security.MessageDigest.getInstance("SHA-256");
        bytes = unicode2native(char(text), "UTF-8");
        chunk = typecast(uint8(bytes(:)), "int8");
        if ~isempty(chunk)
            engine.update(chunk, 0, numel(chunk));
        end
        raw = typecast(engine.digest(), "uint8");
        digest = lower(string(reshape(dec2hex(raw, 2)', 1, [])));
        end
        end

        function paths = saveAllFigures(results, cfg, directory)
        paths = [
            localResponse(results, directory)
            localRobustness(results, cfg, directory)
            localCca(results, directory)
            localTrajectory(results.trajectoryTracking, directory)
        ];
        function paths = localResponse(results, directory)
        scenarios = unique(results.response.Scenario, "stable");
        paths = strings(numel(scenarios), 1);
        for i = 1:numel(scenarios)
            scenario = scenarios(i);
            indices = find(results.response.Scenario == scenario);
            [projection, target] = localContract(scenario);
            [fig, ax] = newPlot();
            for j = indices'
                run = results.responseResults{j};
                primary = projection' * run.states(1:3, :);
                plot(ax, run.timeS, primary, LineWidth=1.5, DisplayName=run.controller);
            end
            yline(ax, target, "k--", LineWidth=1.2, DisplayName="reference");
            xlabel(ax, "Time (s)");
            ylabel(ax, localLabel(scenario));
            whiteLegend(ax, Location="best");
            title(ax, compose("%s regulation response", scenario));
            paths(i) = exportPlot(fig, ax, directory, "response_" + scenario);
        end
        end
        
        function [projection, target] = localContract(scenario)
        switch scenario
            case "x"
                projection = [1; 0; 0];
                target = 1;
            case "y"
                projection = [0; 1; 0];
                target = 1;
            case "diagonal"
                projection = [1; 1; 0] / sqrt(2);
                target = sqrt(2);
            case "yaw"
                projection = [0; 0; 1];
                target = pi / 2;
            otherwise
                error("cca:study:ScenarioPlot", "Unknown scenario %s.", scenario);
        end
        end
        
        function label = localLabel(scenario)
        if scenario == "yaw"
            label = "Yaw (rad)";
        else
            label = "Projected position (m)";
        end
        end
        
        function paths = localRobustness(results, cfg, directory)
        paths = strings(4, 1);
        summary = results.robustnessDevelopment.summary;
        paths(1) = localGrouped(summary, "SettlingTimeS", "Settling time (s)", ...
            "robustness_development_settling", directory);
        paths(2) = localGrouped(summary, "OvershootPercent", "Overshoot (%)", ...
            "robustness_development_overshoot", directory);
        paths(3) = localConfirmationSpeed(results.robustnessConfirmation, cfg, directory);
        paths(4) = localConfirmationEnvelope(results.robustnessConfirmation, directory);
        end
        
        function path = localGrouped(summary, metric, label, name, directory)
        cases = unique(summary.PlantCase, "stable");
        values = zeros(numel(cases), 2);
        for i = 1:numel(cases)
            rows = summary(summary.PlantCase == cases(i), :);
            values(i, 1) = rows{rows.Controller == "LQR", metric};
            values(i, 2) = rows{rows.Controller == "NMPC", metric};
        end
        [fig, ax] = newPlot();
        displayCases = replace(cases, "_", " ");
        bar(ax, categorical(displayCases, displayCases), values);
        ylabel(ax, label);
        xlabel(ax, "Physical case");
        whiteLegend(ax, ["LQR", "NMPC"], Location="best");
        title(ax, replace(name, "_", " "));
        path = exportPlot(fig, ax, directory, name);
        end
        
        function path = localConfirmationSpeed(study, cfg, directory)
        rows = study.summary(study.summary.Controller == "NMPC", :);
        values = zeros(height(rows), 1);
        for i = 1:height(rows)
            run = study.results{2 * i};
            wheel = cca.Model.matrices(cfg.robot).wheelKinematics * run.states(4:6, :);
            values(i) = max(abs(wheel), [], "all");
        end
        [fig, ax] = newPlot();
        displayCases = replace(rows.PlantCase, "_", " ");
        bars = bar(ax, categorical(displayCases, displayCases), values);
        bars.DisplayName = "NMPC peak";
        yline(ax, max(cfg.actuator.wheelSpeedMaxRadps), "r--", ...
            LineWidth=1.4, DisplayName="physical limit");
        ylabel(ax, "Peak wheel speed (rad/s)");
        xlabel(ax, "Seeded confirmation case");
        whiteLegend(ax, Location="best");
        title(ax, "Held-out physical wheel-speed transfer");
        path = exportPlot(fig, ax, directory, ...
            "robustness_confirmation_wheel_speed");
        end
        
        function path = localConfirmationEnvelope(study, directory)
        [fig, ax] = newPlot();
        projection = [1; 1; 0] / sqrt(2);
        rows = study.summary(study.summary.Controller == "NMPC", :);
        for i = 1:height(rows)
            run = study.results{2 * i};
            plot(ax, run.timeS, projection' * run.states(1:3, :), ...
                LineWidth=1.1, DisplayName=replace(rows.PlantCase(i), "_", " "));
        end
        yline(ax, sqrt(2), "k--", LineWidth=1.2, DisplayName="reference");
        xlabel(ax, "Time (s)");
        ylabel(ax, "Projected position (m)");
        whiteLegend(ax, Location="bestoutside");
        title(ax, "Held-out NMPC transient envelope");
        path = exportPlot(fig, ax, directory, ...
            "robustness_confirmation_transients");
        end
        
        function paths = localCca(results, directory)
        paths = strings(2, 1);
        [fig, ax] = newPlot();
        for i = 1:numel(results.stochastic.results)
            run = results.stochastic.results{i};
            margin = min(run.physicalMarginM, [], 1);
            plot(ax, run.timeS, margin, LineWidth=1.5, DisplayName=run.controller);
        end
        yline(ax, 0, "--", Color=[0.75, 0.10, 0.10], ...
            LineWidth=1.2, DisplayName="collision boundary");
        xlabel(ax, "Time (s)");
        ylabel(ax, "Minimum physical margin (m)");
        whiteLegend(ax, Location="best");
        title(ax, "Matched crossing physical margin");
        paths(1) = exportPlot(fig, ax, directory, ...
            "cca_crossing_physical_margin");
        
        summary = results.contextAblation.summary;
        labels = replace(summary.Controller, "_", " ") + ...
            " | " + replace(summary.ContextMode, "_", " ");
        [fig, ax] = newPlot();
        bar(ax, categorical(labels, labels), summary.MinimumPhysicalMarginM, ...
            FaceColor=[0.12, 0.47, 0.71], EdgeColor=[0, 0, 0]);
        ylabel(ax, "Minimum physical margin (m)");
        xlabel(ax, "Controller and context mode");
        title(ax, "Context-mechanism ablation");
        paths(2) = exportPlot(fig, ax, directory, ...
            "cca_context_ablation_margin");
        end
        
        function paths = localTrajectory(study, directory)
        paths = strings(3, 1);
        nmpc = study.results{2};
        [fig, ax] = newPlot();
        plot(ax, nmpc.desiredStates(1, :), nmpc.desiredStates(2, :), ...
            "k--", LineWidth=1.5, DisplayName="reference");
        plot(ax, nmpc.states(1, :), nmpc.states(2, :), ...
            LineWidth=1.7, DisplayName="NMPC truth");
        plot(ax, nmpc.estimatedStates(1, :), nmpc.estimatedStates(2, :), ...
            ":", Color=[0.25, 0.25, 0.25], LineWidth=1.3, ...
            DisplayName="NMPC EKF estimate");
        axis(ax, "equal");
        xlabel(ax, "x position (m)");
        ylabel(ax, "y position (m)");
        title(ax, "NMPC figure-eight trajectory tracking");
        whiteLegend(ax, Location="best");
        paths(1) = exportPlot(fig, ax, directory, ...
            "trajectory_tracking_xy");
        
        [fig, ax] = newPlot();
        ax.YScale = "log";
        for i = 1:numel(study.results)
            run = study.results{i};
            error = vecnorm(run.states(1:2, :) - run.desiredStates(1:2, :));
            plot(ax, run.timeS, max(error, 1e-4), LineWidth=1.5, ...
                DisplayName=run.controller);
        end
        xlabel(ax, "Time (s)");
        ylabel(ax, "Position tracking error (m)");
        title(ax, "Matched trajectory-tracking error");
        whiteLegend(ax, Location="best");
        paths(2) = exportPlot(fig, ax, directory, ...
            "trajectory_tracking_error");
        
        [fig, ax] = newPlot();
        error = vecnorm(nmpc.estimatedStates(1:2, :) - nmpc.states(1:2, :));
        sigma = zeros(size(nmpc.timeS));
        for k = 1:numel(nmpc.timeS)
            sigma(k) = 2 * sqrt(trace(nmpc.estimationCovariance(1:2, 1:2, k)));
        end
        plot(ax, nmpc.timeS, error, LineWidth=1.5, ...
            DisplayName="position estimation error");
        plot(ax, nmpc.timeS, sigma, "k--", LineWidth=1.3, ...
            DisplayName="2 sqrt(trace(Pxy))");
        xlabel(ax, "Time (s)");
        ylabel(ax, "Position estimation error (m)");
        title(ax, "EKF state-estimation envelope");
        whiteLegend(ax, Location="best");
        paths(3) = exportPlot(fig, ax, directory, ...
            "trajectory_ekf_estimation");
        end
        
        function [figureHandle, axesHandle] = newPlot()
        figureHandle = figure(Visible="off", Color=[1, 1, 1], ...
            Position=[100, 100, 900, 560]);
        figureHandle.InvertHardcopy = "off";
        axesHandle = axes(figureHandle);
        axesHandle.Color = [1, 1, 1];
        axesHandle.XColor = [0, 0, 0];
        axesHandle.YColor = [0, 0, 0];
        axesHandle.GridColor = [0.72, 0.72, 0.72];
        axesHandle.MinorGridColor = [0.86, 0.86, 0.86];
        axesHandle.ColorOrder = [
            0.0000, 0.4470, 0.7410
            0.8500, 0.3250, 0.0980
            0.4660, 0.6740, 0.1880
            0.4940, 0.1840, 0.5560
            0.3010, 0.7450, 0.9330
            0.6350, 0.0780, 0.1840
        ];
        hold(axesHandle, "on");
        grid(axesHandle, "on");
        box(axesHandle, "on");
        axesHandle.FontName = "Times New Roman";
        axesHandle.FontSize = 12;
        axesHandle.TickLabelInterpreter = "none";
        axesHandle.Title.Color = [0, 0, 0];
        axesHandle.XLabel.Color = [0, 0, 0];
        axesHandle.YLabel.Color = [0, 0, 0];
        end
        
        function path = exportPlot(figureHandle, axesHandle, directory, name)
        path = fullfile(directory, name + ".png");
        exportgraphics(axesHandle, path, Resolution=200, BackgroundColor="white");
        close(figureHandle);
        end
        
        function handle = whiteLegend(axesHandle, varargin)
        handle = legend(axesHandle, varargin{:});
        handle.Color = [1, 1, 1];
        handle.TextColor = [0, 0, 0];
        handle.EdgeColor = [0, 0, 0];
        handle.Box = "on";
        handle.Interpreter = "none";
        end
        
        end

        function path = writeManifest(output, artifacts, cfg, gates, requireGate)
        
        sourceRoot = string(fileparts(fileparts(mfilename("fullpath"))));
        sourceFiles = [dir(fullfile(sourceRoot, "+cca", "**", "*.m")); ...
            dir(fullfile(sourceRoot, "run_studies.m")); ...
            dir(fullfile(sourceRoot, "run_tests.m")); ...
            dir(fullfile(sourceRoot, "setup_project.m"))];
        fullNames = reshape( ...
            string(fullfile({sourceFiles.folder}, {sourceFiles.name})), [], 1);
        [fullNames, order] = sort(fullNames);
        sourceFiles = sourceFiles(order);
        sourceTokens = strings(numel(sourceFiles), 1);
        sourceRootNormalized = replace(sourceRoot, "\", "/");
        for i = 1:numel(sourceFiles)
            fullNameNormalized = replace(fullNames(i), "\", "/");
            relative = erase(fullNameNormalized, sourceRootNormalized + "/");
            sourceTokens(i) = relative + ":" + localSha256File(fullNames(i));
        end
        
        artifactHashes = strings(numel(artifacts), 1);
        artifactNames = strings(numel(artifacts), 1);
        outputNormalized = strip(replace(string(output), "\", "/"), "right", "/");
        for i = 1:numel(artifacts)
            artifactNormalized = replace(string(artifacts(i)), "\", "/");
            artifactNames(i) = erase(artifactNormalized, outputNormalized + "/");
            artifactHashes(i) = localSha256File(artifacts(i));
        end
        
        manifest.schema = "continuous-cca-nmpc-matlab-gate-a-v3";
        manifest.generatedUtc = string(datetime("now", TimeZone="UTC", ...
            Format="yyyy-MM-dd'T'HH:mm:ss'Z'"));
        manifest.matlabVersion = string(version);
        manifest.platform = string(computer);
        installed = ver;
        manifest.toolboxes = struct( ...
            "name", {installed.Name}, "version", {installed.Version});
        manifest.configVersion = cfg.meta.version;
        manifest.configProvenance = cfg.meta.provenance;
        manifest.configSha256 = localSha256Text(jsonencode(cfg));
        manifest.randomSeed = cfg.meta.seed;
        manifest.confirmationSeed = 27072027;
        manifest.sourceSha256 = localSha256Text(strjoin(sourceTokens, newline));
        [manifest.gitHead, manifest.gitDirty] = localGitState( ...
            fullfile(sourceRoot, "..", ".."));
        manifest.numericGatePass = gates.Pass(end);
        manifest.requireGate = requireGate;
        if isfield(cfg.study, "profile")
            manifest.studyProfile = cfg.study.profile;
        else
            manifest.studyProfile = "full";
        end
        if requireGate && gates.Pass(end)
            manifest.evidenceStatus = "verified-numerical-gate";
        else
            manifest.evidenceStatus = "candidate-development-only";
        end
        manifest.realTimeReady = false;
        manifest.hardwareValidated = false;
        manifest.contextCalibrationValid = false;
        manifest.assumptions = [
            "simulation parameters are not identified hardware values"
            "robot feedback uses a six-state EKF with synthetic noisy measurements"
            "applied torque is available to the prediction model in MATLAB"
            "fmincon timing is offline and misses the 50 ms deadline"
            "confirmation is a seeded synthetic envelope, not an invariance proof"
        ];
        manifest.artifacts = struct( ...
            "path", cellstr(artifactNames), "sha256", cellstr(artifactHashes));
        path = fullfile(output, "manifest.json");
        file = fopen(path, "w");
        assert(file >= 0, "cca:study:Manifest", "Cannot open manifest for writing.");
        cleanup = onCleanup(@() fclose(file));
        fprintf(file, "%s\n", jsonencode(manifest, PrettyPrint=true));
        clear cleanup
        function digest = localSha256File(path)
        engine = java.security.MessageDigest.getInstance("SHA-256");
        file = fopen(path, "r");
        assert(file >= 0, "cca:study:Hash", "Cannot open file for hashing.");
        cleanup = onCleanup(@() fclose(file));
        while ~feof(file)
            bytes = fread(file, 8192, "*uint8");
            if ~isempty(bytes)
                chunk = typecast(bytes(:), "int8");
                engine.update(chunk, 0, numel(chunk));
            end
        end
        raw = typecast(engine.digest(), "uint8");
        digest = lower(string(reshape(dec2hex(raw, 2)', 1, [])));
        clear cleanup
        end
        
        function digest = localSha256Text(text)
        engine = java.security.MessageDigest.getInstance("SHA-256");
        bytes = unicode2native(char(text), "UTF-8");
        chunk = typecast(uint8(bytes(:)), "int8");
        if ~isempty(chunk)
            engine.update(chunk, 0, numel(chunk));
        end
        raw = typecast(engine.digest(), "uint8");
        digest = lower(string(reshape(dec2hex(raw, 2)', 1, [])));
        end
        
        function [head, dirty] = localGitState(repository)
        [headStatus, headText] = system( ...
            "git -C """ + repository + """ rev-parse HEAD");
        [dirtyStatus, dirtyText] = system( ...
            "git -C """ + repository + """ status --porcelain");
        if headStatus == 0
            head = strip(string(headText));
        else
            head = "unavailable";
        end
        dirty = dirtyStatus ~= 0 || strlength(strip(string(dirtyText))) > 0;
        end
        
        end
    end
end
