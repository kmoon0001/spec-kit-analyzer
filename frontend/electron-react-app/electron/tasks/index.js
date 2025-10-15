const path = require('node:path');
const { TaskManager } = require('./taskManager');

const registerDefaultTasks = (manager) => {
  manager.register('analysis', path.join('workers', 'analysisWorker.js'));
  manager.register('mock', path.join('workers', 'mockHeavyWorker.js'));
  return manager;
};

const createTaskManager = (options = {}) => registerDefaultTasks(new TaskManager(options));

const taskManager = createTaskManager();

module.exports = {
  taskManager,
  createTaskManager,
  registerDefaultTasks,
};
