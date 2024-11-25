export const utils = {
  getCollectionId: function() {
    return collection_id;
  },

  removeProtocol: function(url) {
    return url.replace(/(^\w+:|^)\/\//, '');
  },

  getSelection: function() {
    var text = "";
    if (window.getSelection) {
        text = window.getSelection().toString();
    } else if (document.selection && document.selection.type != "Control") {
        text = document.selection.createRange().text;
    }

    console.log("Selected Text:", text); // Debugging line to check selected text
    return text;
  },

  handleAjaxState: function() {
    $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
  }
};
