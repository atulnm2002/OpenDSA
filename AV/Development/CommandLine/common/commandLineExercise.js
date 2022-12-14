import { createCommandsMap } from "./commandHandlers.js";
import { CommandHistory } from "./commandHistory.js";
import { initializeCommandLine } from "./commandLine.js";
import {
  renderFileStructureVisualization,
  renderGitVisualization,
  updateFileStructureVisualization,
  updateGitVisualization,
} from "./fileStructure.js";
import { Directory } from "./fileSystemEntity.js";
import { Branch, Commit } from "./gitClasses.js";
import { FILE_STATE, GIT_STATE } from "./gitStatuses.js";

const DEFAULT_FILE_STRUCTURE = {
  name: "/",
  contents: [
    "bird.txt",
    "snake.txt",
    "fish.txt",
    {
      name: "mammals",
      contents: [
        "monkey.txt",
        "mouse.txt",
        "bear.txt",
        {
          name: "dogs",
          contents: ["beagle.txt", "boxer.txt", "poodle.txt"],
        },
      ],
    },
  ],
};

const DEFAULT_GIT_FILE_STRUCTURE = {
  name: "/",
  contents: [
    "README",
    ".gitignore",
    {
      name: "src",
      contents: ["index.html", "app.js", "config.js"],
    },
  ],
};

const DEFAULT_CWD_INDEX_PATH = [3];

function initializeCommandLineExercise(
  text,
  handleAwardCredit,
  awardCreditCommand,
  initialFileStructure,
  initialCwdIndexPath
) {
  // Load the config object with interpreter and code created by odsaUtils.js
  //   const config = ODSA.UTILS.loadConfig();
  const config = ODSA.UTILS.loadConfig(),
    interpret = config.interpreter; // get the interpreter

  updateText(text);

  const homeDir = new Directory(
    initialFileStructure ? initialFileStructure : DEFAULT_FILE_STRUCTURE
  );

  let currDir = homeDir.followIndexPath(
    initialCwdIndexPath ? initialCwdIndexPath : DEFAULT_CWD_INDEX_PATH
  );

  let svgData;

  function getHomeDir() {
    return homeDir;
  }

  function getCurrDir() {
    return currDir;
  }

  function setCurrDir(dir) {
    currDir = dir;
  }

  function getSvgData() {
    return svgData;
  }

  updateCommandLinePrompt(getCurrDir());

  const commandsMap = createCommandsMap(
    getSvgData,
    getCurrDir,
    setCurrDir,
    getHomeDir,
    updateFileStructureVisualization
  );

  let resizeCount = 0;

  // new ResizeObserver(() => {
  //   if (resizeCount === 1) {
  setTimeout(() => {
    const id = "#visualization-container";
    const visualizationWidth = $(id).width();
    const visualizationHeight = $(id).height();
    svgData = renderFileStructureVisualization(
      homeDir,
      currDir.id,
      visualizationWidth,
      visualizationHeight,
      id
    );
    //this is sloppy but I was having sizing issues
  }, 500);
  // }
  // else if (resizeCount > 1) {
  //   updateTree();
  // }
  resizeCount++;
  // }).observe(document.querySelector("#visualization-container"));

  const awardCreditHandler = {};
  if (Array.isArray(awardCreditCommand)) {
    awardCreditCommand.forEach((command) => {
      awardCreditHandler[command] = handleAwardCredit(getCurrDir, getHomeDir);
    });
  } else {
    awardCreditHandler[awardCreditCommand] = handleAwardCredit(
      getCurrDir,
      getHomeDir
    );
  }

  const commandHistory = new CommandHistory();

  initializeCommandLine(
    "#arrayValues",
    "#history",
    commandsMap,
    awardCreditHandler,
    ["git", "vi"],
    getCurrDir,
    commandHistory
  );
}

function initializeGitExercise(
  text,
  handleAwardCredit,
  awardCreditCommand,
  initialFileStructure,
  initialCwdIndexPath
) {
  // Load the config object with interpreter and code created by odsaUtils.js
  //   const config = ODSA.UTILS.loadConfig();
  const config = ODSA.UTILS.loadConfig(),
    interpret = config.interpreter; // get the interpreter

  updateText(text);

  const localHomeDir = new Directory(DEFAULT_GIT_FILE_STRUCTURE);
  let localCurrDir = localHomeDir.followIndexPath([]);

  const remoteHomeDir = localHomeDir.copyWithGitId();

  const localInitialCommit = new Commit();
  let localCurrBranch = new Branch("main");
  localInitialCommit.insertBranch(localCurrBranch);

  const remoteInitialCommit = localInitialCommit.copy();
  let remoteCurrBranch = remoteInitialCommit.branches[0];

  localHomeDir.setState(GIT_STATE.COMMITTED, FILE_STATE.UNCHANGED);
  remoteHomeDir.setState(GIT_STATE.COMMITTED, FILE_STATE.UNCHANGED);

  let svgData;

  function getLocalHomeDir() {
    return localHomeDir;
  }

  function getLocalCurrDir() {
    return localCurrDir;
  }

  function setLocalCurrDir(dir) {
    localCurrDir = dir;
  }

  function getRemoteHomeDir() {
    return remoteHomeDir;
  }

  function getLocalInitialCommit() {
    return localInitialCommit;
  }

  function setLocalInitialCommit(commit) {
    localInitialCommit = commit;
  }

  function getLocalCurrBranch() {
    return localCurrBranch;
  }

  function setLocalCurrBranch(branch) {
    localCurrBranch = branch;
  }

  function getRemoteInitialCommit() {
    return remoteInitialCommit;
  }

  function getRemoteCurrBranch() {
    return remoteCurrBranch;
  }

  function setRemoteCurrBranch(branch) {
    remoteCurrBranch = branch;
  }

  function getSvgData() {
    return svgData;
  }

  const gitMethods = {
    getRemoteHomeDir,
    getLocalInitialCommit,
    getLocalCurrBranch,
    setLocalCurrBranch,
    getRemoteInitialCommit,
    getRemoteCurrBranch,
    setRemoteCurrBranch,
    setLocalInitialCommit,
  };

  const commandsMap = createCommandsMap(
    getSvgData,
    getLocalCurrDir,
    setLocalCurrDir,
    getLocalHomeDir,
    updateGitVisualization,
    //TODO decouple this later
    gitMethods
  );

  let resizeCount = 0;

  // new ResizeObserver(() => {
  //   if (resizeCount === 1) {
  setTimeout(() => {
    const id = "#visualization-container";
    const visualizationWidth = $(id).width();
    const visualizationHeight = $(id).height();
    const d3Data = localHomeDir.mapToD3();
    svgData = renderGitVisualization(
      getLocalHomeDir(),
      gitMethods,
      visualizationWidth,
      visualizationHeight,
      id
    );
    //this is sloppy but I was having sizing issues
  }, 500);
  // }
  // else if (resizeCount > 1) {
  //   updateTree();
  // }
  resizeCount++;
  // }).observe(document.querySelector("#visualization-container"));

  const awardCreditHandler = {};
  awardCreditHandler[awardCreditCommand] = handleAwardCredit(
    getLocalCurrDir,
    getLocalHomeDir
  );

  initializeCommandLine(
    "#arrayValues",
    "#history",
    commandsMap,
    awardCreditHandler
  );
}

function updateText(text) {
  $("#command-title").text(text.commandTitle);
  $("#command-description").text(text.commandDescription);
  $("#challenge-description").text(text.challengeDescription);
}

function awardCredit() {
  $("#success-message").removeClass("hidden").addClass("visible");
  ODSA.AV.awardCompletionCredit();
}

function updateCommandLinePrompt(currDir) {
  $("#command-line-prompt").text(createCommandLinePrompt(currDir));
}

function createCommandLinePrompt(currDir) {
  return `${currDir.getPath()} $`;
}
export {
  initializeCommandLineExercise,
  initializeGitExercise,
  awardCredit,
  updateCommandLinePrompt,
};
