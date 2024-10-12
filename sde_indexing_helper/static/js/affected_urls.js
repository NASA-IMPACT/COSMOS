var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;

$(document).ready(function () {
  handleAjaxStartAndStop();
  initializeDataTable();
  // Conditionally add the button based on patternType
  if (patternType == "Exclude") {
    $("#affectedURLsTable")
      .DataTable()
      .button()
      .add(0, {
        text: "Add Include Pattern",
        className: "addPattern",
        action: function () {
          $modal = $("#includePatternModal").modal();
        },
      });
  }
  setupClickHandlers();
});

function handleAjaxStartAndStop() {
  $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
}

function initializeDataTable() {
  var affected_urls_table = $("#affectedURLsTable").DataTable({
    processing: true,
    pageLength: 100,
    colReorder: true,
    stateSave: true,
    serverSide: true,
    orderCellsTop: true,
    pagingType: "input",
    paging: true,
    rowId: "url",
    layout: {
      bottomEnd: "inputPaging",
      topEnd: null,
      topStart: {
        info: true,
        pageLength: {
          menu: [
            [25, 50, 100, 500],
            ["Show 25", "Show 50", "Show 100", "Show 500"],
          ],
        },
        buttons: [],
      },
    },
    columnDefs: [
      { orderable: true, targets: "_all" },
      { orderable: false, targets: "filter-row" },
    ],
    orderCellsTop: true,
    ajax: {
      url: (function () {
        let url = null;
        if (patternType === "Exclude") {
          url = `/api/exclude-pattern-affected-urls/?format=datatables&pattern_id=${pattern_id}`;
        } else if (patternType === "Include") {
          url = `/api/include-pattern-affected-urls/?format=datatables&pattern_id=${pattern_id}`;
        } else if (patternType === "Title") {
          url = `/api/title-pattern-affected-urls/?format=datatables&pattern_id=${pattern_id}`;
        } else if (patternType === "Document Type") {
          url = `/api/documenttype-pattern-affected-urls/?format=datatables&pattern_id=${pattern_id}`;
        }
        return url;
      })(),
      data: function (d) {},
      complete: function (xhr, status) {},
    },
    createdRow: function (row, data, dataIndex) {
      // Set data-sort attribute based on the included property
      const dataSortValue = data.included ? "1" : "0";
      $(row).find("td").eq(2).attr("data-sort", dataSortValue);
      if (patternType === "Exclude" && data["included"]) {
        $(row).attr(
          "style",
          "background-color: rgba(255, 61, 87, 0.26) !important"
        );
      }
    },

    columns: [
      { data: "id", searchable: false, class: "whiteText text-center" },
      getURLColumn(),
      ...getConditionalColumns(patternType),
    ],
  });

  $("#affectedURLsFilter").on(
    "beforeinput",
    DataTable.util.debounce(function (val) {
      affected_urls_table.columns(1).search(this.value).draw();
    }, 1000)
  );
}

function getURLColumn() {
  return {
    data: "url",
    width: "30%",
    render: function (data, type, row) {
      return `<div class="url-cell"><span class="candidate_url nameStyling">${data}</span>
              <a target="_blank" href=${data} data-url="/api/candidate-urls/${row["id"]}/" class="url-link">
              <i class="material-icons url-icon">open_in_new</i></a>
              </div>`;
    },
  };
}

function getIncludeURLColumn() {
  return {
    data: "included",
    width: "30%",
    render: function (data, type, row) {
      return `<a class="include-url-btn" data-url-id=${row["id"]} value=${
        row["url"]
      } included_by_pattern='${row["included_by_pattern"]}' match_pattern_id='${
        row["match_pattern_id"]
      }'>
              ${
                data
                  ? '<i class="material-icons tick-mark" style="color: green">check</i>'
                  : '<i class="material-icons cross-mark" style="color: red">close</i>'
              }
              </a>`;
    },
    class: "col-3 text-center",
  };
}

function getConditionalColumns(patternType) {
  // add these columns if patternType is "Exclude"
  if (patternType === "Exclude") {
    return [
      getIncludeURLColumn(),
      { data: "included_by_pattern", visible: false, searchable: false },
      { data: "match_pattern_id", visible: false, searchable: false },
      { data: "excluded", visible: false, searchable: false },
    ];
  }
  return [];
}

function setupClickHandlers() {
  handleHideorShowSubmitButton();
  handleHideorShowKeypress();
  handleIncludeIndividualUrlClick();
}

function handleIncludeIndividualUrlClick() {
  $("#affectedURLsTable").on("click", ".include-url-btn", function () {
    const inclusion_status = this.querySelector("i");
    if (inclusion_status.classList.contains("cross-mark")) {
      match_pattern = remove_protocol($(this).attr("value"));
      match_pattern_type = INDIVIDUAL_URL;

      postIncludePatterns(match_pattern, match_pattern_type)
        .then((result) => {
          // refresh the table after a pattern is added
          $("#affectedURLsTable").DataTable().ajax.reload(null, false);
        })
        .catch((error) => {
          toastr.error("Error:", error);
        });
    } else {
      var url = $(this).attr("value");
      var included_by_pattern = $(this).attr("included_by_pattern");
      var match_pattern_id = $(this).attr("match_pattern_id");

      if (included_by_pattern === remove_protocol(url)) {
        currentURLtoDelete = `/api/include-patterns/${match_pattern_id}/`;
        deletePattern(currentURLtoDelete, (data_type = "Include Pattern"));
        toastr.success("URL excluded successfully");
      } else {
        toastr.error(
          "This URL is affected by a multi-URL include pattern: " +
            included_by_pattern
        );
      }
    }
  });
}

function postIncludePatterns(match_pattern, match_pattern_type = 0) {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: "/api/include-patterns/",
      type: "POST",
      data: {
        collection: collection_id,
        match_pattern: match_pattern,
        match_pattern_type: match_pattern_type,
        csrfmiddlewaretoken: csrftoken,
      },
      success: function (data) {
        toastr.success("Added to include patterns successfully");
        resolve({
          id: data.id,
          match_pattern: data.match_pattern,
        });
      },
      error: function (xhr, status, error) {
        var errorMessage = xhr.responseText;
        toastr.error(errorMessage);
        reject(error);
      },
    });
  });
}

function remove_protocol(url) {
  return url.replace(/(^\w+:|^)\/\//, "");
}

function deletePattern(
  url,
  data_type,
  url_type = null,
  candidate_urls_count = null
) {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: url,
      type: "DELETE",
      data: {
        csrfmiddlewaretoken: csrftoken,
      },
      headers: {
        "X-CSRFToken": csrftoken,
      },
      success: function (data) {
        // refresh the table after a pattern is deleted
        $("#affectedURLsTable").DataTable().ajax.reload(null, false);
      },
      error: function (xhr, status, error) {
        var errorMessage = xhr.responseText;
        toastr.error(errorMessage);
      },
    });
  });
}

function handleHideorShowKeypress() {
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

  $("body").on("click", ".modal-backdrop", function () {
    $("#hideShowColumnsModal").modal("hide");
  });

  //adding each modals keypress functionalities
  addEnterEscapeKeypress("#includePatternModal", "#include_pattern_form");
}

//template to add enter and escape functionalities to add pattern modals
function addEnterEscapeKeypress(modalID, formID) {
  $("body").on("keydown", function (event) {
    let modal = $(modalID);
    let form = $(formID);
    if (event.key == "Escape" && modal.is(":visible")) {
      modal.modal("hide");
    }
    if (event.key == "Enter" && modal.is(":visible")) {
      form.submit();
      modal.modal("hide");
    }
  });
}

function handleHideorShowSubmitButton() {
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
}

$("#include_pattern_form").on("submit", function (e) {
  e.preventDefault();

  // check if pattern already exists
  input_serialized = $(this).serializeArray();
  $.ajax({
    url: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
    type: "GET",
    success: function (response) {
      var existingPatterns = response.data.map((item) => item.match_pattern);
      if (existingPatterns.includes(input_serialized[0].value)) {
        toastr.warning("Pattern already exists");
        $("#includePatternModal").modal("hide");
        return;
      } else {
        // if pattern does not exist, create a new pattern
        inputs = {};
        input_serialized.forEach((field) => {
          inputs[field.name] = field.value;
        });

        postIncludePatterns(
          (match_pattern = inputs.match_pattern),
          (match_pattern_type = 2)
        )
          .then(() => {
            // Reload the DataTable after the successful postIncludePatterns call
            $("#affectedURLsTable").DataTable().ajax.reload(null, false);
          })
          .catch((error) => {
            toastr.error("Error posting include patterns:", error);
          });
      }
    },
    error: function (xhr, status, error) {
      toastr.error("An error occurred while checking existing patterns");
    },
  });

  // close the modal if it is open
  $("#includePatternModal").modal("hide");
});
