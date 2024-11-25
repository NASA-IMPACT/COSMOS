import { initializeTables } from './modules/tables.js';
import { api } from './modules/api.js';
import { eventHandlers } from './modules/eventHandlers.js';
import { utils } from './modules/utils.js';
import { columnRenderers } from './modules/columnRenderers.js';

const DeltaUrlManager = {
  init: function() {
    this.collection_id = utils.getCollectionId();
    this.setupGlobalState();
    this.initializeTables();
    this.setupEventHandlers();
  },

  setupGlobalState: function() {
    utils.handleAjaxState();
    this.state = {
      selectedText: '',
      newIncludePatternsCount: 0,
      newExcludePatternsCount: 0,
      newTitlePatternsCount: 0,
      newDocumentTypePatternsCount: 0,
      currentTab: '',
      uniqueId: null
    };
  },

  initializeTables: function() {
    this.tables = {
      deltaUrls: initializeTables.deltaUrls(this.collection_id),
      curatedUrls: initializeTables.curatedUrls(this.collection_id),
      excludePatterns: initializeTables.excludePatterns(this.collection_id),
      includePatterns: initializeTables.includePatterns(this.collection_id),
      titlePatterns: initializeTables.titlePatterns(this.collection_id),
      documentTypePatterns: initializeTables.documentTypePatterns(this.collection_id),
      divisionPatterns: initializeTables.divisionPatterns(this.collection_id)
    };
  },

  setupEventHandlers: function() {
    eventHandlers.setupHandlers();
  }
};

// Initialize when document is ready
$(document).ready(function() {
  DeltaUrlManager.init();
});
