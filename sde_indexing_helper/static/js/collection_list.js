let table = $("#collection_table").DataTable({
  paging: false,
  stateSave: true,
  orderCellsTop: true,
  dom: "BPfritip",
  buttons: [
    "csv",
    {
      text: "JSON",
      action: function (e, dt, button, config) {
        var data = dt.buttons.exportData();

        $.fn.dataTable.fileSave(
          new Blob([JSON.stringify(data)]),
          "collections.json"
        );
      },
    },
  ],
  initComplete: function (data) {
    // logic for dropdown filters here
  },
  columnDefs: [
    {
      searchPanes: {
        options: [
          {
            label: "0 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[3]).text() == 0;
            },
          },
          {
            label: "1 solo URL",
            value: function (rowData, rowIdx) {
              return $(rowData[3]).text() == 1;
            },
          },
          {
            label: "1 to 100 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[3]).text() <= 100 && $(rowData[3]).text() > 1;
            },
          },
          {
            label: "100 to 1,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[3]).text() <= 1000 && $(rowData[3]).text() > 100;
            },
          },
          {
            label: "1,000 to 10,000 URLs",
            value: function (rowData, rowIdx) {
              return (
                $(rowData[3]).text() <= 10000 && $(rowData[3]).text() > 1000
              );
            },
          },
          {
            label: "10,000 to 100,000 URLs",
            value: function (rowData, rowIdx) {
              return (
                $(rowData[3]).text() <= 100000 && $(rowData[3]).text() > 10000
              );
            },
          },
          {
            label: "Over 100,000 URLs",
            value: function (rowData, rowIdx) {
              return $(rowData[3]).text() > 100000;
            },
          },
        ],
      },
      targets: [3],
      type: "num-fmt",
    },
  ],
});

$("#nameFilter").on("keyup", function () {
  table.columns(0).search(this.value).draw();
});

$("#urlFilter").on("keyup", function () {
  table.columns(1).search(this.value).draw();
});

$("#divisionFilter").on("keyup", function () {
  table.columns(2).search(this.value).draw();
});

$("#connectorTypeFilter").on("keyup", function () {
  table.columns(6).search(this.value).draw();
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function handleCurationStatusSelect() {
  $("body").on("click", ".curation_status_select", function () {
    var collection_id = $(this).data("collection-id");
    var curation_status = $(this).attr("value");
    var curation_status_text = $(this).text();
    var color_choices = {
      1: "btn-light",
      2: "btn-danger",
      3: "btn-warning",
      4: "btn-info",
      5: "btn-success",
      6: "btn-primary",
      7: "btn-info",
      8: "btn-secondary",
    };

    $possible_buttons = $("body").find(
      `[id="curation-status-button-${collection_id}"]`
    );
    if ($possible_buttons.length > 1) {
      $button = $possible_buttons[1];
      $button = $($button);
    } else {
      $button = $(`#curation-status-button-${collection_id}`);
    }
    $button.text(curation_status_text);
    $button.removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
    );
    $button.addClass(color_choices[parseInt(curation_status)]);
    $("#collection_table").DataTable().searchPanes.rebuildPane(6);

    postCurationStatus(collection_id, curation_status);
  });
}

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
      5: "btn-info",
      6: "btn-primary",
      7: "btn-success",
      8: "btn-secondary",
      9: "btn-light",
      10: "btn-danger",
      11: "btn-warning",
      12: "btn-info",
      13: "btn-secondary",
      14: "btn-success",
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
    $("#collection_table").DataTable().searchPanes.rebuildPane(6);

    postWorkflowStatus(collection_id, workflow_status);
  });
}

function handleCuratorSelect() {
  $("body").on("click", ".curator_select", function () {
    var collection_id = $(this).data("collection-id");
    var curator_id = $(this).attr("value");
    var curator_text = $(this).text();

    $(`#curator-button-${collection_id}`).text(curator_text);
    $(`#curator-button-${collection_id}`).removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary"
    );
    $(`#curator-button-${collection_id}`).addClass("btn-success");

    postCurator(collection_id, curator_id);
  });
}

function postCurationStatus(collection_id, curation_status) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      curation_status: curation_status,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Curation Status Updated!");
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
});

function setupClickHandlers() {
  handleCurationStatusSelect();
  handleWorkflowStatusSelect();
  handleCuratorSelect();
}
