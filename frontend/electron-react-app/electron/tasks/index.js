const path = require('node:path');
const { TaskManager } = require('./taskManager');

const taskManager = new TaskManager();

taskManager.register('analysis', path.join('workers', 'analysisWorker.js'));

taskManager.register('mock', path.join('workers', 'mockHeavyWorker.js'));

module.exports = {
  taskManager,
};
