function results = run_tests()
%RUN_TESTS Execute only the clean CCA-NMPC rebuild test suite.

root = setup_project();
repositoryRoot = fileparts(root);
suite = testsuite(fullfile(repositoryRoot, "tests", "matlab"), ...
    IncludeSubfolders=true);
results = run(suite);
disp(table(results));
assertSuccess(results);
end
