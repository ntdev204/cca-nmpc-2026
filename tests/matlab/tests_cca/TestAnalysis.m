classdef TestAnalysis < matlab.unittest.TestCase
    methods (Test)
        function openLoopProperties(testCase)
            cfg = cca.defaults();
            report = cca.AnalysisTools.openLoop(cfg);
            testCase.verifyEqual(report.continuousControllabilityRank, 6);
            testCase.verifyEqual(report.controllabilityRank, 6);
            testCase.verifyEqual(report.inputRank, 3);
            testCase.verifyEqual(report.inputNullity, 1);
            testCase.verifyLessThan(report.nullspaceResidual, 1e-12);
            testCase.verifyLessThan(report.equilibriumResidual, 1e-12);
            testCase.verifyLessThan(report.powerDualityResidual, 1e-12);
            testCase.verifyGreaterThan(report.minimumInputSingularValue, 0);
            testCase.verifyLessThanOrEqual(report.zohStateMatrixError, ...
                cfg.study.zohParityTolerance);
            testCase.verifyLessThanOrEqual(report.zohInputMatrixError, ...
                cfg.study.zohParityTolerance);
            testCase.verifyTrue(report.zohParityPass);
        end

        function lqrCertificate(testCase)
            cfg = cca.defaults();
            certificate = cca.AnalysisTools.stability(cfg);
            testCase.verifyTrue(certificate.pass);
            testCase.verifyLessThan(certificate.maxPoleMagnitude, 1);
            testCase.verifyLessThan( ...
                certificate.maximumTerminalResidualEigenvalue, 0);
            testCase.verifyLessThanOrEqual( ...
                certificate.maximumSampledIncrease, 0);
        end

        function responseMetricSanity(testCase)
            t = (0:0.01:5)';
            y = 1 - exp(-2 * t);
            metrics = cca.AnalysisTools.responseMetrics(t, y, 1, 0.02);
            testCase.verifyGreaterThan(metrics.riseTimeS, 0);
            testCase.verifyGreaterThan(metrics.settlingTimeS, 0);
            testCase.verifyLessThan(metrics.overshootPercent, 1e-12);
            testCase.verifyLessThan(abs(metrics.steadyStateError), 1e-3);
        end

        function openLoopChannelAllocation(testCase)
            cfg = cca.defaults();
            rows = cca.AnalysisTools.openLoopChannels(cfg);
            testCase.verifyEqual(height(rows), 3);
            testCase.verifyLessThan( ...
                max(rows.WrenchAllocationResidual), 1e-10);
            testCase.verifyLessThan( ...
                max(rows.NominalCrossAxisRate), 1e-10);
        end

        function openLoopPulseIsBoundedAndDecays(testCase)
            cfg = cca.defaults();
            rows = cca.AnalysisTools.openLoopPulseChannels(cfg);
            testCase.verifyEqual(height(rows), 3);
            testCase.verifyLessThan( ...
                max(rows.WrenchAllocationResidual), 1e-10);
            testCase.verifyGreaterThan(min(rows.NominalPeakRate), 0);
            testCase.verifyLessThan( ...
                max(abs(rows.NominalFinalRate)), ...
                max(rows.NominalPeakRate));
        end

        function numericalIntegrationParity(testCase)
            cfg = cca.defaults();
            report = cca.AnalysisTools.numericalParity(cfg);
            testCase.verifyEqual( ...
                report.fineSubsteps, cfg.study.numericalParitySubsteps);
            testCase.verifyTrue(report.pass);
        end

        function empiricalRoaGrid(testCase)
            cfg = cca.defaults();
            cfg.study.roaGridPointsPerAxis = 3;
            report = cca.AnalysisTools.regionOfAttraction(cfg);
            testCase.verifyEqual(report.GridCases, 27);
            testCase.verifyGreaterThan(report.ConvergenceRate, 0);
            testCase.verifyEqual(report.WheelSpeedViolationCases, 0);
        end

        function terminalEnforcedLocalNmpc(testCase)
            cfg = cca.defaults();
            report = cca.AnalysisTools.localNmpcStability(cfg);
            testCase.verifyTrue(report.Pass);
            testCase.verifyEqual(report.FirstSolveSuccessRate, 1);
            testCase.verifyEqual(report.RecursiveSolveSuccessRate, 1);
        end

        function nullspaceTorqueOnlyWastesEffortInReducedModel(testCase)
            cfg = cca.defaults();
            report = cca.AnalysisTools.overActuation(cfg);
            testCase.verifyLessThan(report.NullShiftedWrenchResidual, 1e-12);
            testCase.verifyGreaterThan( ...
                report.NullShiftedSquaredEffort, report.MinimumSquaredEffort);
            testCase.verifyLessThan(report.MaximumStateDifference, 1e-12);
            testCase.verifyLessThan(report.NullShiftedTorqueHeadroomNm, ...
                report.MinimumTorqueHeadroomNm);
        end

        function feedbackRejectsMismatchBetterThanPlanReplay(testCase)
            cfg = cca.defaults();
            study = cca.AnalysisTools.feedbackNecessity(cfg);
            replay = study.summary(2, :);
            feedback = study.summary(3, :);
            testCase.verifyLessThan(feedback.FinalProjectedError, ...
                replay.FinalProjectedError);
            testCase.verifyLessThan(feedback.ProjectedIAE, replay.ProjectedIAE);
        end
    end
end
