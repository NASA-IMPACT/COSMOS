// CSRF token and collection_id
var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var collection_id = getCollectionId();
var selected_text = "";
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;
var newIncludePatternsCount = 0;
var newExcludePatternsCount = 0;
var newTitlePatternsCount = 0;
var newDocumentTypePatternsCount = 0;
var currentTab = ""; //blank for the first tab
var matchPatternTypeMap = {
  "Individual URL Pattern": 1,
  "Multi-URL Pattern": 2,
};
var uniqueId; //used for logic related to contents on column customization modal

//fix table allignment when changing around tabs
$('a[data-toggle="tab"]').on("shown.bs.tab", function (e) {
  currentTab = e.target.id;
  $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
});

$(document).ready(function () {
  handleAjaxStartAndStop();
  initializeDataTable();
  setupClickHandlers();
});

function handleAjaxStartAndStop() {
  $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
}

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
    if (column.visible() === false) return;
    var columnName = column.header().textContent.trim();
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
        candidateTableHeaderDefinitons[columnName]
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

function initializeDataTable() {
  var true_icon = '<i class="material-icons" style="color: green">check</i>';
  var false_icon = '<i class="material-icons" style="color: red">close</i>';

  var candidate_urls_table = $("#candidate_urls_table").DataTable({
    // scrollY: true,
    lengthMenu: [
      [25, 50, 100, 500],
      ["Show 25", "Show 50", "Show 100", "Show 500"],
    ],
    pageLength: 100,
    stateSave: true,
    serverSide: true,
    orderCellsTop: true,
    pagingType: "input",
    dom: "ilBrtip",
    buttons: [
      "spacer",
      "csv",
      "spacer",
      {
        text: "Customize Columns",
        className: "customizeColumns",
        action: function () {
          modalContents("#candidate_urls_table");
        },
      },
    ],
    select: {
      style: "os",
      selector: "td:nth-child(5)",
    },
    rowId: "url",
    stateLoadCallback: function (settings) {
      var state = JSON.parse(
        localStorage.getItem(
          "DataTables_candidate_urls_" + window.location.pathname
        )
      );
      if (!state) {
        settings.oInit.pageLength = 1;
      }
      return state;
    },
    ajax: {
      url: `/api/candidate-urls/?format=datatables&collection_id=${collection_id}`,
      data: function (d) {
        d.is_excluded = $("#filter-checkbox").is(":checked") ? false : null;
      },
    },
    initComplete: function (data) {
      const addDropdownSelect = [1, 4, 5];
      const dict = {
        1: "Images",
        2: "Data",
        3: "Documentation",
        4: "Software and Tools",
        5: "Missions and Instruments",
        6: "Training and Education",
      };
      this.api()
        .columns()
        .every(function (index) {
          let column = this;
          if (addDropdownSelect.includes(index)) {
            $("thead tr td select.dropdown-" + index).on("change", function () {
              var val = $.fn.dataTable.util.escapeRegex($(this).val());
              column.search(val ? "^" + val + "$" : "", true, false).draw();
            });
          }
        });
    },

    columns: [
      getURLColumn(),
      getExcludedColumn(true_icon, false_icon),
      getScrapedTitleColumn(),
      getGeneratedTitleColumn(),
      getDocumentTypeColumn(),
      { data: "id", visible: false, searchable: false },
      { data: "generated_title_id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false, searchable: false },
      { data: "candidate_urls_count", visible: false, searchable: false },
      { data: "excluded", visible: false, searchable: false },
    ],
    createdRow: function (row, data, dataIndex) {
      if (data["excluded"]) {
        $(row).attr("style", "background-color: #ab387d !important");
      }
    },
  });

  $("#candidateUrlFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      candidate_urls_table.columns(0).search(this.value).draw();
    }, 1000)
  );

  $("#candidateScrapedTitleFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      candidate_urls_table.columns(2).search(this.value).draw();
    }, 1000)
  );

  $("#candidateNewTitleFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      candidate_urls_table.columns(3).search(this.value).draw();
    }, 1000)
  );

  var exclude_patterns_table = $("#exclude_patterns_table").DataTable({
    // scrollY: true,
    serverSide: true,
    dom: "lBrtip",
    buttons: [
      {
        text: "Add Pattern",
        className: "addPattern",
        action: function () {
          $modal = $("#excludePatternModal").modal();
        },
      },
      {
        text: "Customize Columns",
        className: "customizeColumns",
        action: function () {
          modalContents("#exclude_patterns_table");
        },
      },
    ],
    lengthMenu: [
      [25, 50, 100, 500],
      ["Show 25", "Show 50", "Show 100", "Show 500"],
    ],
    orderCellsTop: true,
    pageLength: 100,
    ajax: `/api/exclude-patterns/?format=datatables&collection_id=${collection_id}`,
    initComplete: function (data) {
      var table = $("#exclude_patterns_table").DataTable();

      this.api()
        .columns()
        .every(function (index) {
          let column = this;
          if (column.data().length === 0) {
            $("#exclude-patterns-dropdown-1").prop("disabled", true);
          } else if (index === 1) {
            $("#exclude-patterns-dropdown-1").on("change", function () {
              if ($(this).val() === "") table.columns(6).search("").draw();
              else {
                table
                  .column(6)
                  .search(matchPatternTypeMap[$(this).val()])
                  .draw();
              }
            });
          }
        });
    },
    columns: [
      { data: "match_pattern", class: "whiteText" },
      {
        data: "match_pattern_type_display",
        class: "text-center whiteText",
        sortable: true,
      },
      { data: "reason", class: "text-center whiteText", sortable: false },
      {
        data: "candidate_urls_count",
        class: "text-center whiteText",
        sortable: false,
      },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-exclude-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false },
    ],
  });

  $("#candidateMatchPatternFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      exclude_patterns_table.columns(0).search(this.value).draw();
    }, 1000)
  );

  $("#candidateReasonFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      exclude_patterns_table.columns(2).search(this.value).draw();
    }, 1000)
  );

  var include_patterns_table = $("#include_patterns_table").DataTable({
    // scrollY: true,
    lengthMenu: [
      [25, 50, 100, 500],
      ["Show 25", "Show 50", "Show 100", "Show 500"],
    ],
    dom: "lBrtip",
    buttons: [
      {
        text: "Add Pattern",
        className: "addPattern",
        action: function () {
          $modal = $("#includePatternModal").modal();
        },
      },
      {
        text: "Customize Columns",
        className: "customizeColumns",
        action: function () {
          modalContents("#include_patterns_table");
        },
      },
    ],
    pageLength: 100,
    orderCellsTop: true,
    serverSide: true,
    ajax: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
    initComplete: function (data) {
      var table = $("#include_patterns_table").DataTable();
      this.api()
        .columns()
        .every(function (index) {
          let column = this;
          if (column.data().length === 0) {
            $("#include-patterns-dropdown-1").prop("disabled", true);
          } else {
            if (index === 1) {
              $("#include-patterns-dropdown-1").on("change", function () {
                if ($(this).val() === "") table.columns(5).search("").draw();
                table
                  .column(5)
                  .search(matchPatternTypeMap[$(this).val()])
                  .draw();
              });
            }
          }
        });
    },
    columns: [
      { data: "match_pattern", class: "whiteText" },
      {
        data: "match_pattern_type_display",
        class: "text-center whiteText",
        sortable: false,
      },
      {
        data: "candidate_urls_count",
        class: "text-center whiteText",
        sortable: false,
      },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-include-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false },
    ],
  });

  $("#candidateIncludeMatchPatternFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      include_patterns_table.columns(0).search(this.value).draw();
    }, 1000)
  );

  var title_patterns_table = $("#title_patterns_table").DataTable({
    // scrollY: true,
    serverSide: true,
    dom: "lBrtip",
    buttons: [
      {
        text: "Add Pattern",
        className: "addPattern",
        action: function () {
          $modal = $("#titlePatternModal").modal();
        },
      },
      {
        text: "Customize Columns",
        className: "customizeColumns",
        action: function () {
          modalContents("#title_patterns_table");
        },
      },
    ],
    lengthMenu: [
      [25, 50, 100, 500],
      ["Show 25", "Show 50", "Show 100", "Show 500"],
    ],
    pageLength: 100,
    orderCellsTop: true,
    ajax: `/api/title-patterns/?format=datatables&collection_id=${collection_id}`,
    initComplete: function (data) {
      var table = $("#title_patterns_table").DataTable();

      this.api()
        .columns()
        .every(function (index) {
          let column = this;
          if (column.data().length === 0) {
            $("#title-patterns-dropdown-1").prop("disabled", true);
          } else if (index === 1) {
            $("#title-patterns-dropdown-1").on("change", function () {
              if ($(this).val() === "") table.columns(6).search("").draw();
              else {
                table
                  .column(6)
                  .search(matchPatternTypeMap[$(this).val()])
                  .draw();
              }
            });
          }
        });
    },
    columns: [
      { data: "match_pattern", class: "whiteText" },
      {
        data: "match_pattern_type_display",
        class: "text-center whiteText",
        sortable: false,
      },
      { data: "title_pattern", class: "whiteText" },
      {
        data: "candidate_urls_count",
        class: "text-center whiteText",
        sortable: false,
      },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-title-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false },
    ],
  });

  $("#candidateTitleMatchPatternFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      title_patterns_table.columns(0).search(this.value).draw();
    }, 1000)
  );

  $("#candidateTitlePatternTypeFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      title_patterns_table.columns(2).search(this.value).draw();
    }, 1000)
  );

  var document_type_patterns_table = $(
    "#document_type_patterns_table"
  ).DataTable({
    // scrollY: true,
    dom: "lBrtip",
    buttons: [
      {
        text: "Add Pattern",
        className: "addPattern",
        action: function () {
          $modal = $("#documentTypePatternModal").modal();
        },
      },
      {
        text: "Customize Columns",
        className: "customizeColumns",
        action: function () {
          modalContents("#document_type_patterns_table");
        },
      },
    ],
    serverSide: true,
    lengthMenu: [
      [25, 50, 100, 500],
      ["Show 25", "Show 50", "Show 100", "Show 500"],
    ],
    orderCellsTop: true,
    pageLength: 100,
    ajax: `/api/document-type-patterns/?format=datatables&collection_id=${collection_id}`,
    initComplete: function (data) {
      this.api()
        .columns()
        .every(function (index) {
          var table = $("#document_type_patterns_table").DataTable();

          let addDropdownSelect = {
            1: {
              columnToSearch: 6,
              matchPattern: {
                "Individual URL Pattern": 1,
                "Multi-URL Pattern": 2,
              },
            },
            2: {
              columnToSearch: 7,
              matchPattern: {
                Images: 1,
                Data: 2,
                Documentation: 3,
                "Software and Tools": 4,
                "Missions and Instruments": 5,
                "Training and Education": 6,
              },
            },
          };

          let column = this;
          if (column.data().length === 0) {
            $(`#document-type-patterns-dropdown-${index}`).prop(
              "disabled",
              true
            );
          } else if (index in addDropdownSelect) {
            $("#document-type-patterns-dropdown-" + index).on(
              "change",
              function () {
                let col = addDropdownSelect[index].columnToSearch;
                let searchInput =
                  addDropdownSelect[index].matchPattern[$(this).val()];
                if ($(this).val() === "" || $(this).val() === undefined)
                  table.columns(col).search("").draw();
                else {
                  table.columns(col).search(searchInput).draw();
                }
              }
            );
          }
        });
    },

    columns: [
      { data: "match_pattern", class: "whiteText" },
      {
        data: "match_pattern_type_display",
        class: "text-center whiteText",
        sortable: false,
      },
      { data: "document_type_display", class: "whiteText" },
      {
        data: "candidate_urls_count",
        class: "text-center whiteText",
        sortable: false,
      },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-document-type-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false },
      { data: "document_type", visible: false },
    ],
  });

  $("#candidateDocTypeMatchPatternFilter").on(
    "keyup",
    DataTable.util.debounce(function (val) {
      document_type_patterns_table.columns(0).search(this.value).draw();
    }, 1000)
  );
}

function handleTabsClick() {
  $("#includePatternsTab").on("click", function () {
    newIncludePatternsCount = 0;
    $("#includePatternsTab").html(`Include Patterns`);
  });
  $("#excludePatternsTab").on("click", function () {
    newExcludePatternsCount = 0;
    $("#excludePatternsTab").html(`Exclude Patterns`);
  });
  $("#titlePatternsTab").on("click", function () {
    newTitlePatternsCount = 0;
    $("#titlePatternsTab").html(`Title Patterns`);
  });
  $("#documentTypePatternsTab").on("click", function () {
    newDocumentTypePatternsCount = 0;
    $("#documentTypePatternsTab").html(`Document Type Patterns`);
  });
}

function setupClickHandlers() {
  handleHideorShowSubmitButton();
  handleAddNewPatternClick();

  handleDeleteDocumentTypeButtonClick();
  handleDeleteExcludePatternButtonClick();
  handleDeleteIncludePatternButtonClick();
  handleDeleteTitlePatternButtonClick();

  handleDocumentTypeSelect();
  handleExcludeIndividualUrlClick();
  handleNewTitleChange();

  handleUrlLinkClick();
  handleTabsClick();

  handleWorkflowStatusSelect();
}

function getURLColumn() {
  return {
    data: "url",
    render: function (data, type, row) {
      return `<a target="_blank" href="${data}" data-url="/api/candidate-urls/${
        row["id"]
      }/" class="url_link"> <i class="material-icons whiteText">open_in_new</i></a> <span class="candidate_url nameStyling">${remove_protocol(
        data
      )}</span>`;
    },
  };
}

function getScrapedTitleColumn() {
  return {
    data: "scraped_title",
    render: function (data, type, row) {
      return `<span class="whiteText">${data}</span>`;
    },
  };
}

function getGeneratedTitleColumn() {
  return {
    data: "generated_title",
    render: function (data, type, row) {
      return `<input type="text" class="form-control individual_title_input whiteText" value='${data}' data-generated-title-id=${
        row["generated_title_id"]
      } data-match-pattern-type=${
        row["match_pattern_type"]
      } data-candidate-urls-count=${
        row["candidate_urls_count"]
      } data-url=${remove_protocol(row["url"])} />`;
    },
  };
}

function getExcludedColumn(true_icon, false_icon) {
  return {
    data: "excluded",
    class: "col-1 text-center",
    render: function (data, type, row) {
      return data === true
        ? `<a class="exclude_individual_url" value=${remove_protocol(
            row["url"]
          )}>${true_icon}</a>`
        : `<a class="exclude_individual_url" value=${remove_protocol(
            row["url"]
          )}>${false_icon}</a>`;
    },
  };
}

function getDocumentTypeColumn() {
  return {
    data: "document_type",
    render: function (data, type, row) {
      var dict = {
        1: "Images",
        2: "Data",
        3: "Documentation",
        4: "Software and Tools",
        5: "Missions and Instruments",
        6: "Training and Education",
      };
      button_text = data ? dict[data] : "Select";
      button_color = data ? "btn-success" : "btn-secondary";
      return `
            <div class="dropdown document_type_dropdown " data-match-pattern=${remove_protocol(
              row["url"]
            )}>
              <button class="btn ${button_color} btn-sm dropdown-toggle selectStyling" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                ${button_text}
              </button>
              <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                <a class="dropdown-item document_type_select" href="#" value="0">None</a>
                <a class="dropdown-item document_type_select" href="#" value="1">Images</a>
                <a class="dropdown-item document_type_select" href="#" value="2">Data</a>
                <a class="dropdown-item document_type_select" href="#" value="3">Documentation</a>
                <a class="dropdown-item document_type_select" href="#" value="4">Software and Tools</a>
                <a class="dropdown-item document_type_select" href="#" value="5">Missions and Instruments</a>
                <a class="dropdown-item document_type_select" href="#" value="6">Training and Education</a>
              </div>
            </div>`;
    },
  };
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

function handleDocumentTypeSelect() {
  $("body").on("click", ".document_type_select", function () {
    $match_pattern = $(this)
      .parents(".document_type_dropdown")
      .data("match-pattern");
    postDocumentTypePatterns(
      $match_pattern,
      (match_pattern_type = 1),
      (document_type = $(this).attr("value"))
    );
  });
}

function handleUrlPartButton() {
  $(".url_part_button").on("click", function () {
    postExcludePatterns($(this).attr("value"));
  });
}

function handleExcludeIndividualUrlClick() {
  $("body").on("click", ".exclude_individual_url", function () {
    postExcludePatterns(
      (match_pattern = $(this).attr("value")),
      (match_pattern_type = 1),
      true
    );
  });
}

function handleDeleteExcludePatternButtonClick() {
  $("body").on("click", ".delete-exclude-pattern-button", function () {
    row_id = $(this).data("row-id");
    deletePattern(
      `/api/exclude-patterns/${row_id}/`,
      (data_type = "Exclude Pattern")
    );
  });
}

function handleDeleteIncludePatternButtonClick() {
  $("body").on("click", ".delete-include-pattern-button", function () {
    row_id = $(this).data("row-id");
    deletePattern(
      `/api/include-patterns/${row_id}/`,
      (data_type = "Include Pattern")
    );
  });
}

function handleDeleteTitlePatternButtonClick() {
  $("body").on("click", ".delete-title-pattern-button", function () {
    row_id = $(this).data("row-id");
    deletePattern(
      `/api/title-patterns/${row_id}/`,
      (data_type = "Title Pattern")
    );
  });
}

function handleDeleteDocumentTypeButtonClick() {
  $("body").on("click", ".delete-document-type-pattern-button", function () {
    row_id = $(this).data("row-id");
    deletePattern(
      `/api/document-type-patterns/${row_id}/`,
      (data_type = "Document Type Pattern")
    );
  });
}

function handleAddNewPatternClick() {
  $("body").on("click", ".add_new_pattern", function () {
    var pattern = $(this).parents(".pattern_row").find("input").val();
    postExcludePatterns(pattern);
  });
}

function handleNewTitleChange() {
  $("body").on("change", ".individual_title_input", function () {
    var match_pattern = $(this).data("url");
    var title_pattern = $(this).val();
    var generated_title_id = $(this).data("generated-title-id");
    var match_pattern_type = $(this).data("match-pattern-type");
    var candidate_urls_count = $(this).data("candidate-urls-count");
    if (!title_pattern) {
      deletePattern(
        `/api/title-patterns/${generated_title_id}/`,
        (data_type = "Title Pattern"),
        (url_type = match_pattern_type),
        (candidate_urls_count = candidate_urls_count)
      );
    } else {
      postTitlePatterns(
        match_pattern,
        title_pattern,
        (match_pattern_type = 1),
        (title_pattern_type = 1)
      );
    }
  });
}

function handleUrlLinkClick() {
  $("body").on("click", ".url_link", function (event) {
    var url = $(this).attr("data-url");
    postVisited(url);
    $(this)
      .closest("tr")
      .find(".visited_icon")
      .css("color", "green")
      .text("done");
  });
}

function postDocumentTypePatterns(
  match_pattern,
  match_pattern_type,
  document_type
) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to add document type.");
    return;
  }

  $.ajax({
    url: "/api/document-type-patterns/",
    type: "POST",
    data: {
      collection: collection_id,
      match_pattern: match_pattern,
      match_pattern_type: match_pattern_type,
      document_type: document_type,
      csrfmiddlewaretoken: csrftoken,
    },
    success: function (data) {
      $("#candidate_urls_table").DataTable().ajax.reload(null, false);
      $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
      if(currentTab === ""){ //Only add a notification if we are on the first tab
      newDocumentTypePatternsCount = newDocumentTypePatternsCount + 1;
      $("#documentTypePatternsTab").html(
        `Document Type Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
          newDocumentTypePatternsCount + " new" + 
          `</span>`
      );
    }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function postExcludePatterns(match_pattern, match_pattern_type = 0, force) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to exclude.");
    return;
  }
  if(!force){ //If the user clicked the icon in the table, we make the change regardless
  // if pattern exists in table already (unless another pattern overrules it)
  var table = $("#exclude_patterns_table").DataTable();
  var itemIdColumnData = table.column(0).data().toArray();
  if (itemIdColumnData.includes(match_pattern)) {
    toastr.success("Pattern already exists");
    return;
  }
}

  $.ajax({
    url: "/api/exclude-patterns/",
    type: "POST",
    data: {
      collection: collection_id,
      match_pattern: match_pattern,
      match_pattern_type: match_pattern_type,
      csrfmiddlewaretoken: csrftoken,
    },
    success: function (data) {
      $("#candidate_urls_table").DataTable().ajax.reload(null, false);
      $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
      if(currentTab === ""){ //Only add a notification if we are on the first tab
      newExcludePatternsCount = newExcludePatternsCount + 1;
      $("#excludePatternsTab").html(
        `Exclude Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
          newExcludePatternsCount + " new" + 
          `</span>`
      );
    }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function postIncludePatterns(match_pattern, match_pattern_type = 0) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to include.");
    return;
  }

  // if pattern exists in table already
  var table = $("#include_patterns_table").DataTable();
  var itemIdColumnData = table.column(0).data().toArray();
  if (itemIdColumnData.includes(match_pattern)) {
    toastr.success("Pattern already exists");
    return;
  }

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
      $("#candidate_urls_table").DataTable().ajax.reload(null, false);
      $("#include_patterns_table").DataTable().ajax.reload(null, false);
      if(currentTab === ""){ //Only add a notification if we are on the first tab
      newIncludePatternsCount = newIncludePatternsCount + 1;
      $("#includePatternsTab").html(
        `Include Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
          newIncludePatternsCount + " new" + 
          `</span>`
      );
    }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function postTitlePatterns(
  match_pattern,
  title_pattern,
  match_pattern_type = 1
) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to change the title.");
    return;
  }

  $.ajax({
    url: "/api/title-patterns/",
    type: "POST",
    data: {
      collection: collection_id,
      match_pattern: match_pattern,
      match_pattern_type: match_pattern_type,
      title_pattern: title_pattern,
      csrfmiddlewaretoken: csrftoken,
    },
    success: function (data) {
      $("#candidate_urls_table").DataTable().ajax.reload(null, false);
      $("#title_patterns_table").DataTable().ajax.reload(null, false);
      if(currentTab === ""){ //Only add a notification if we are on the first tab
      newTitlePatternsCount = newTitlePatternsCount + 1;
      $("#titlePatternsTab").html(
        `Title Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
          newTitlePatternsCount + " new" + 
          `</span>`
      );
    }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function postVisited(url) {
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      visited: true,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {},
  });
}

function deletePattern(
  url,
  data_type,
  url_type = null,
  candidate_urls_count = null
) {
  if (url_type === MULTI_URL_PATTERN) {
    var confirmDelete = confirm(
      `YOU ARE ATTEMPTING TO DELETE A MULTI-URL PATTERN. THIS WILL AFFECT ${candidate_urls_count} URLs. \n\nAre you sure you want to do this? Currently there is no way to delete a single URL from a Multi-URL pattern`
    );
  } else {
    var confirmDelete = confirm(
      `Are you sure you want to delete this ${data_type}?`
    );
  }
  if (!confirmDelete) {
    return;
  }
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
      $("#candidate_urls_table").DataTable().ajax.reload(null, false);
      $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
      $("#include_patterns_table").DataTable().ajax.reload(null, false);
      $("#title_patterns_table").DataTable().ajax.reload(null, false);
      $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
    },
  });
}

function getCollectionId() {
  return collection_id;
}

function getParameterByName(name, url) {
  if (!url) url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
    results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return "";
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function remove_protocol(url) {
  return url.replace(/(^\w+:|^)\/\//, "");
}

function add_exclude_pattern(pattern) {
  var input = $(
    `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" />
                    </div>
                    <div class="col">
                        <button type="button" class="btn btn-success btn-sm add_new_pattern">
                            ✔
                        </button>
                    </div>
                </div>
            `
  );
  $("#exclude_patterns").append(input);
}

// Trigger action when the contexmenu is about to be shown
$("body").on("contextmenu", ".candidate_url", function (event) {
  // Avoid the real one
  event.preventDefault();

  // Show contextmenu
  $(".custom-menu")
    .finish()
    .toggle(100)
    // In the right position (the mouse)
    .css({
      top: event.pageY + "px",
      left: event.pageX - 80 + "px",
    });
});

// If the document is clicked somewhere
$(document).bind("mousedown", function (e) {
  selected_text = get_selection();

  // If the clicked element is not the menu
  if (!$(e.target).parents(".custom-menu").length > 0) {
    // Hide it
    $(".custom-menu").hide(100);
  }
});

function get_selection() {
  var text = "hey";
  if (window.getSelection) {
    text = window.getSelection().toString();
  } else if (document.selection && document.selection.type != "Control") {
    text = document.selection.createRange().text;
  }

  return text;
}

function title_pattern_form(selected_text) {
  $modal = $("#titlePatternModal").modal();
  $modal.find("#match_pattern_input").val(selected_text);
}

function document_type_pattern_form(selected_text) {
  $modal = $("#documentTypePatternModal").modal();
  $modal.find("#match_pattern_input").val(selected_text);
}

// If the menu element is clicked
$(".custom-menu li").click(function () {
  // This is the triggered action name
  switch ($(this).attr("data-action")) {
    case "exclude-pattern":
      postExcludePatterns(selected_text.trim(), (match_pattern_type = 2));
      break;
    case "title-pattern":
      title_pattern_form(selected_text.trim());
      break;
    case "document-type-pattern":
      document_type_pattern_form(selected_text.trim());
      break;
    case "include-pattern":
      postIncludePatterns(selected_text.trim(), (match_pattern_type = 2));
      break;
  }

  // Hide it AFTER the action was triggered
  $(".custom-menu").hide(100);
});

$("#exclude_pattern_form").on("submit", function (e) {
  e.preventDefault();

  // if pattern exists
  var table = $("#exclude_patterns_table").DataTable();
  var itemIdColumnData = table.column(0).data().toArray();
  input_serialized = $(this).serializeArray();
  if (itemIdColumnData.includes(input_serialized[0].value)) {
    toastr.success("Pattern already exists");
    $("#excludePatternModal").modal("hide");
    return;
  }

  // if pattern does not exist
  inputs = {};
  input_serialized.forEach((field) => {
    inputs[field.name] = field.value;
  });

  postExcludePatterns(
    (match_pattern = inputs.match_pattern),
    (match_pattern_type = 2)
  );

  // close the modal if it is open
  $("#excludePatternModal").modal("hide");
});

$("#include_pattern_form").on("submit", function (e) {
  e.preventDefault();

  // if pattern exists
  var table = $("#include_patterns_table").DataTable();
  var itemIdColumnData = table.column(0).data().toArray();
  input_serialized = $(this).serializeArray();
  if (itemIdColumnData.includes(input_serialized[0].value)) {
    toastr.success("Pattern already exists");
    $("#includePatternModal").modal("hide");
    return;
  }

  // if pattern does not exist
  inputs = {};
  input_serialized.forEach((field) => {
    inputs[field.name] = field.value;
  });

  postIncludePatterns(
    (match_pattern = inputs.match_pattern),
    (match_pattern_type = 2)
  );

  // close the modal if it is open
  $("#includePatternModal").modal("hide");
});

$("#title_pattern_form").on("submit", function (e) {
  e.preventDefault();
  inputs = {};
  input_serialized = $(this).serializeArray();
  input_serialized.forEach((field) => {
    inputs[field.name] = field.value;
  });

  postTitlePatterns(
    (match_pattern = inputs.match_pattern),
    (title_pattern = inputs.title_pattern),
    (match_pattern_type = 2)
  );

  // close the modal if it is open
  $("#titlePatternModal").modal("hide");
});

$(".document_type_form_select").on("click", function (e) {
  e.preventDefault();
  $('input[name="document_type_pattern"]').val($(this).attr("value"));
  inputs = {};
  input_serialized = $(this)
    .parents("#document_type_pattern_form")
    .serializeArray();
  input_serialized.forEach((field) => {
    inputs[field.name] = field.value;
  });

  postDocumentTypePatterns(
    inputs.match_pattern,
    2,
    inputs.document_type_pattern
  );

  // close the modal if it is open
  $("#documentTypePatternModal").modal("hide");
});

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

    $button = $(`#workflow-status-button-${collection_id}`);

    $button.text(workflow_status_text);
    $button.removeClass(
      "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
    );
    $button.addClass(color_choices[parseInt(workflow_status)]);
    postWorkflowStatus(collection_id, workflow_status);
  });
}
