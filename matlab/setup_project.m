function projectRoot = setup_project()
%SETUP_PROJECT Add the project root to the MATLAB path exactly once.

projectRoot = fileparts(mfilename("fullpath"));
if ~contains(path, projectRoot)
    addpath(projectRoot);
end
end

