// Define column constants for better maintainability
const COLUMNS = {
  NAME: 0,
  URL: 1,
  DIVISION: 2,
  DELTA_URLS: 3,
  WORKFLOW_STATUS: 4,
  CURATOR: 5,
  CONNECTOR_TYPE: 6,
  REINDEXING_STATUS: 7,
  REINDEXING_CURATOR: 8,
  WORKFLOW_STATUS_RAW: 9,
  CURATOR_ID: 10,
  REINDEXING_STATUS_RAW: 11,
  REINDEXING_CURATOR_ID: 12
};

var uniqueId; //used for logic related to contents on column customization modal

function modalContents(tableName) {
  var checkboxCount = $("#modalBody input[type='checkbox']").length;

  if (checkboxCount > 0 && tableName === uniqueId) {
    $modal = $("#hideShowColumnsModal").modal({
      backdrop: "static",
      keyboard: true,
    });
    return;
  }

  $modal = $("#hideShowColumnsModal").modal({
    backdrop: "static",
    keyboard: true,
  });
  var table = $(tableName).DataTable();
  if (tableName !== uniqueId) {
    $("#modalBody").html("");
  }
  uniqueId = tableName;

  table.columns().every(function (idx) {
    var column = this;
    var columnName = column.header().textContent.trim();
    if (columnName.length === 0) return;
    var $checkbox = $('<input type="checkbox">')
      .attr({
        id: "checkbox_" + columnName.replace(/\s+/g, "_"), // Generate a unique ID for each checkbox
        name: columnName.replace(/\s+/g, "_"), // Set name attribute for each checkbox
        value: idx,
      })
      .prop("checked", column.visible() ? true : false);
    var $label = $("<label class='whiteText'>")
      .attr("for", "checkbox_" + columnName.replace(/\s+/g, "_"))
      .text(columnName);
    var $caption = $("<p class='headerDescription'>")
      .text(tableHeaderDefinitions[columnName])
      .attr({
        id: "caption",
      });

    var $captionContainer = $("<div>").append($caption);

    var $checkboxContainer = $("<div>")
      .append($checkbox)
      .append($label)
      .addClass("checkbox-wrapper");

    $("#modalBody").append($checkboxContainer);
    $("#modalBody").append($captionContainer);
  });
}

$("body").on("keydown", function () {
  //Close modal via escape
  if (event.key == "Escape" && $("#hideShowColumnsModal").is(":visible")) {
    $("#hideShowColumnsModal").modal("hide");
  }
  //Confirm modal selections via enter
  if (event.key == "Enter" && $("#hideShowColumnsModal").is(":visible")) {
    var table = $(uniqueId).DataTable();
    $("[id^='checkbox_']").each(function () {
      var checkboxValue = $(this).val();
      let column = table.column(checkboxValue);
      var isChecked = $(this).is(":checked");
      if (column.visible() === false && isChecked) column.visible(true);
      else if (column.visible() === true && !isChecked) column.visible(false);
    });
    $("#hideShowColumnsModal").modal("hide");
  }
});

$("body").on("click", "#hideShowSubmitButton", function () {
  var table = $(uniqueId).DataTable();
  $("[id^='checkbox_']").each(function () {
    var checkboxValue = $(this).val();
    let column = table.column(checkboxValue);
    var isChecked = $(this).is(":checked");
    if (column.visible() === false && isChecked) column.visible(true);
    else if (column.visible() === true && !isChecked) column.visible(false);
  });
  $("#hideShowColumnsModal").modal("hide");
});

$("body").on("click", ".modal-backdrop", function () {
  $("#hideShowColumnsModal").modal("hide");
});

let table = $("#collection_table").DataTable({
  paging: false,
  stateSave: true,
  orderCellsTop: true,
  fixedHeader: true,
  layout: {
    topStart: "searchPanes",
  },
  dom: "PiB",
  buttons: [
    {
      text: "Customize Columns",
      className: "customizeColumns",
      action: function () {
        modalContents("#collection_table");
      },
    },
  ],
    searchPanes: {
      controls: true,
      layout: 'columns-6',
      columns: [
        COLUMNS.DIVISION,
        COLUMNS.DELTA_URLS,
        COLUMNS.WORKFLOW_STATUS,
        COLUMNS.CURATOR,
        COLUMNS.CONNECTOR_TYPE,
        COLUMNS.REINDEXING_STATUS
      ]
    },
  
  columnDefs: [
    // hide the data columns
    {
      targets: [COLUMNS.WORKFLOW_STATUS_RAW, COLUMNS.CURATOR_ID, COLUMNS.REINDEXING_STATUS_RAW, COLUMNS.REINDEXING_CURATOR_ID],
      visible: false, width: "0px", responsivePriority: -1
    },
    { width: "200px", targets: COLUMNS.URL },
    {
      searchPanes: {
        options: [
          {
            label: "0 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() == 0;
            },
          },
          {
            label: "1 solo URL",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() == 1;
            },
          },
          {
            label: "1 to 100 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() <= 100 && $(rowData[COLUMNS.DELTA_URLS]).text() > 1;
            },
          },
          {
            label: "100 to 1,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() <= 1000 && $(rowData[COLUMNS.DELTA_URLS]).text() > 100;
            },
          },
          {
            label: "1,000 to 10,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() <= 10000 && $(rowData[COLUMNS.DELTA_URLS]).text() > 1000;
            },
          },
          {
            label: "10,000 to 100,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() <= 100000 && $(rowData[COLUMNS.DELTA_URLS]).text() > 10000;
            },
          },
          {
            label: "Over 100,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[COLUMNS.DELTA_URLS]).text() > 100000;
            },
          },
        ],
      },
      targets: [COLUMNS.DELTA_URLS],
      type: "num-fmt",
    },
    {
      searchPanes: {
        dtOpts: {
          scrollY: "100%",
        },
      },
      targets: [COLUMNS.CURATOR],
    },
    {
      searchPanes: {
        dtOpts: {
          scrollY: "100%",
        },
      },
      targets: [COLUMNS.CONNECTOR_TYPE],
    },
  ],
  autoWidth: false,
});

$("#workflow-status-selector").on("change", function () {
  table
    .columns(COLUMNS.WORKFLOW_STATUS_RAW)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
});

$("#curator-selector").on("change", function () {
  table
    .columns(COLUMNS.CURATOR_ID)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
});

$("#reindexing-status-selector").on("change", function () {
  table
    .columns(COLUMNS.REINDEXING_STATUS_RAW)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
});

// Need to change this to reflect REINDEXING CURATOR CHANGE
$("#reindexing-curator-selector").on("change", function () {
  table
    .columns(COLUMNS.CURATOR_ID)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
});

$("#nameFilter").on("keyup", function () {
  table.columns(COLUMNS.NAME).search(this.value).draw();
});

$("#urlFilter").on("keyup", function () {
  table.columns(COLUMNS.URL).search(this.value).draw();
});

$("#divisionFilter").on("keyup", function () {
  table.columns(COLUMNS.DIVISION).search(this.value).draw();
});

$("#connectorTypeFilter").on("keyup", function () {
  table.columns(COLUMNS.CONNECTOR_TYPE).search(this.value).draw();
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function handleWorkflowStatusSelect() {
  $("body").on("click", ".workflow_status_select", function () {
    var collection_id = $(this).data("collection-id");
    var workflow_status = $(this).attr("value");
    var workflow_status_text = $(this).text();
    var color_choices = {
      1: "btn-light",
      2: "btn-danger",
      3: "btn-warning",
      4: "btn-info",
      5: "btn-success",
      6: "btn-primary",
      7: "btn-info",
      8: "btn-secondary",
      9: "btn-light",
      10: "btn-danger",
      11: "btn-warning",
      12: "btn-info",
      13: "btn-success",
      14: "btn-primary",
      15: "btn-info",
      16: "btn-secondary",
    };

    $possible_buttons = $("body").find(
      `[id="workflow-status-button-${collection_id}"]`
    );
    if ($possible_buttons.length > 1) {
      $button = $possible_buttons[1];
      $button = $($button);
    } else {
      $button = $(`#workflow-status-button-${collection_id}`);
    }
    $button.text(workflow_status_text);
    $button.removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
    );
    $button.addClass(color_choices[parseInt(workflow_status)]);
    var row = table.row("#" + collection_id);
    let index = row.index();
    var $html = $("<div />", { html: table.data()[index][COLUMNS.WORKFLOW_STATUS] });
    $html.find("button").text(workflow_status_text);
    $html
      .find("button")
      .removeClass(
        "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
      );
    $html.find("button").addClass(color_choices[parseInt(workflow_status)]);
    table.data()[index][COLUMNS.WORKFLOW_STATUS] = $html.html();
    $("#collection_table").DataTable().searchPanes.rebuildPane(COLUMNS.WORKFLOW_STATUS);

    postWorkflowStatus(collection_id, workflow_status);
  });
}

function handleReindexingStatusSelect() {
  $("body").on("click", ".reindexing_status_select", function () {
    var collection_id = $(this).data("collection-id");
    var reindexing_status = $(this).attr("value");
    var reindexing_status_text = $(this).text();
    var color_choices = {
      1: "btn-light",     // REINDEXING_NOT_NEEDED
      2: "btn-warning",   // REINDEXING_NEEDED_ON_DEV
      3: "btn-secondary", // REINDEXING_FINISHED_ON_DEV
      4: "btn-info",      // REINDEXING_READY_FOR_CURATION
      5: "btn-warning",   // REINDEXING_CURATION_IN_PROGRESS
      6: "btn-primary",   // REINDEXING_CURATED
      7: "btn-success"    // REINDEXING_INDEXED_ON_PROD
    };

    $possible_buttons = $("body").find(
      `[id="reindexing-status-button-${collection_id}"]`
    );
    if ($possible_buttons.length > 1) {
      $button = $possible_buttons[1];
      $button = $($button);
    } else {
      $button = $(`#reindexing-status-button-${collection_id}`);
    }
    $button.text(reindexing_status_text);
    $button.removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
    );
    $button.addClass(color_choices[parseInt(reindexing_status)]);
    var row = table.row("#" + collection_id);
    let index = row.index();
    var $html = $("<div />", { html: table.data()[index][COLUMNS.REINDEXING_STATUS] });
    $html.find("button").text(reindexing_status_text);
    $html
      .find("button")
      .removeClass(
        "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
      );
    $html.find("button").addClass(color_choices[parseInt(reindexing_status)]);
    table.data()[index][COLUMNS.REINDEXING_STATUS] = $html.html();
    $("#collection_table").DataTable().searchPanes.rebuildPane(COLUMNS.REINDEXING_STATUS);

    postReindexingStatus(collection_id, reindexing_status);
  });
}

function handleCuratorSelect() {
  $("body").on("click", ".curator_select", function () {
    var collection_id = $(this).data("collection-id");
    var curator_id = $(this).attr("value");
    var curator_text = $(this).text();
    $possible_buttons = $("body").find(
      `[id="curator-button-${collection_id}"]`
    );
    if ($possible_buttons.length > 1) {
      $button = $possible_buttons[1];
      $button = $($button);
    } else {
      $button = $(`#curator-button-${collection_id}`);
    }

    $button.text(curator_text);

    $button.removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary"
    );
    $button.addClass("btn-success");
    var row = table.row("#" + collection_id);
    let index = row.index();
    var $html = $("<div />", { html: table.data()[index][COLUMNS.CURATOR] });
    $html.find("button").text(curator_text);
    table.data()[index][COLUMNS.CURATOR] = $html.html();
    table.searchPanes.rebuildPane(COLUMNS.CURATOR);
    postCurator(collection_id, curator_id);
  });
}

function postReindexingStatus(collection_id, reindexing_status) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      reindexing_status: reindexing_status,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Reindexing Status Updated!");
    },
  });
}


function postWorkflowStatus(collection_id, workflow_status) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      workflow_status: workflow_status,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Workflow Status Updated!");
    },
  });
}

function postCurator(collection_id, curator_id) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      curated_by: curator_id,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Curator Updated!");
    },
  });
}

$(document).ready(function () {
  setupClickHandlers();

  // Clear search values and redraw table
  clearSearchValues();

  // Remove the search input and add custom titles
  var paneTitles = [
    "Division",
    "Delta URLs",
    "Workflow Status",
    "Curator",
    "Connector Type",
    "Reindexing Status",
  ];

  // Event listener for the collection search input
  $('#collectionSearch').on('keyup', function () {
    // Get the search query
    let query = $(this).val().toLowerCase();

    // Clear previous search
    table.search('').columns().search('');

    // TODO: this section might still need to be refactored to align with our column index definitions
    // Filter the table based on the query in the collection name and config folder data attribute
    table.rows().every(function () {
      let row = $(this.node());
      let name = row.find('td').first().text().toLowerCase();
      let configFolder = row.data('config-folder').toLowerCase();
      let url = row.find('td').eq(1).text().toLowerCase();

      if (name.includes(query) || configFolder.includes(query) || url.includes(query)) {
        row.show();
      } else {
        row.hide();
      }
    });
  });

  $(".dtsp-searchPane").each(function (index) {
    if ($(this).hasClass("dtsp-hidden")) {
      return;
    }
    // Check if the pane title exists for the current index
    else {
      console.log(index, paneTitles[index])
      if (paneTitles[index]) {
        $(this)
          .find(".dtsp-topRow .dtsp-subRow1")
          .prepend(
            '<div class="custom-pane-title">' + paneTitles[index] + "</div>"
          );
      }
    }
  });
});

function setupClickHandlers() {
  handleWorkflowStatusSelect();
  handleReindexingStatusSelect();
  handleCuratorSelect();
}

function clearSearchValues() {
  let table = $("#collection_table").DataTable();
  table.columns().search("").draw();
}
