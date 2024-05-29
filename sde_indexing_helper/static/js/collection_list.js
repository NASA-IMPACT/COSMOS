var uniqueId; //used for logic related to contents on column customization modal

function modalContents(tableName) {
  var checkboxCount = $("#modalBody input[type='checkbox']").length;

  if (checkboxCount > 0 && tableName === uniqueId) {
    $modal = $("#hideShowColumnsModal").modal();
    return;
  }

  $modal = $("#hideShowColumnsModal").modal();
  var table = $(tableName).DataTable();
  if (tableName !== uniqueId) {
    $("#modalBody").html("");
  }
  uniqueId = tableName;

  table.columns().every(function (idx) {
    var column = this;
    var columnName = column.header().textContent.trim();
    if (!column.visible() || columnName.length === 0) return;
    var $checkbox = $('<input type="checkbox">')
      .attr({
        id: "checkbox_" + columnName.replace(/\s+/g, "_"), // Generate a unique ID for each checkbox
        name: columnName.replace(/\s+/g, "_"), // Set name attribute for each checkbox
        value: idx,
      })
      .prop("checked", true);
    var $label = $("<label>")
      .attr("for", "checkbox_" + columnName.replace(/\s+/g, "_"))
      .text(columnName);

    var $caption = $("<p>")
      .text(
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore."
      )
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

let table = $("#collection_table").DataTable({
  paging: false,
  stateSave: true,
  orderCellsTop: true,
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
  columnDefs: [
    {
      targets: 8,
      visible: false,
    },
    { width: "200px", targets: 1 },    {
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
    {
      searchPanes: {
        show: false,
      },
      targets: [7, 8],
    },
  ],
});

$("#collection-dropdown-4").on("change", function () {
  table
    .columns(7)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
});

$("#collection-dropdown-5").on("change", function () {
  table
    .columns(8)
    .search(this.value ? "^" + this.value + "$" : "", true, false)
    .draw();
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

// I don't think this function is being used
// function handleCurationStatusSelect() {
//     $("body").on("click", ".curation_status_select", function () {
//         var collection_id = $(this).data('collection-id');
//         var curation_status = $(this).attr('value');
//         var curation_status_text = $(this).text();
//         var color_choices = {
//             1: "btn-light",
//             2: "btn-danger",
//             3: "btn-warning",
//             4: "btn-info",
//             5: "btn-success",
//             6: "btn-primary",
//             7: "btn-info",
//             8: "btn-secondary",
//         }

//         $possible_buttons = $('body').find(`[id="curation-status-button-${collection_id}"]`);
//         if ($possible_buttons.length > 1) {
//             $button = $possible_buttons[1];
//             $button = $($button);
//         } else {
//             $button = $(`#curation-status-button-${collection_id}`);
//         }
//         $button.text(curation_status_text);
//         $button.removeClass('btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary');
//         $button.addClass(color_choices[parseInt(curation_status)]);
//         $('#collection_table').DataTable().searchPanes.rebuildPane(6);
//         var collection_division = $(this).data('collection-division');
//         postCurationStatus(collection_id, curation_status, collection_division);
//     });
// }

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
    var $html = $("<div />", { html: table.data()[index][4] });
    $html.find("button").html(workflow_status_text);
    $html
      .find("button")
      .removeClass(
        "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
      );
    $html.find("button").addClass(color_choices[parseInt(workflow_status)]);
    table.data()[index][4] = $html.html();
    $("#collection_table").DataTable().searchPanes.rebuildPane(4);

    postWorkflowStatus(collection_id, workflow_status);
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
    var $html = $("<div />", { html: table.data()[index][5] });
    $html.find("button").html(curator_text);
    table.data()[index][5] = $html.html();
    table.searchPanes.rebuildPane(5);
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
  // handleCurationStatusSelect();
  handleWorkflowStatusSelect();
  handleCuratorSelect();
}
