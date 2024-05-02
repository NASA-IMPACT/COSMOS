// CSRF token and collection_id
var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var collection_id = getCollectionId();
var selected_text = "";
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;

$(document).ready(function () {
  handleAjaxStartAndStop();
  initializeDataTable();
  setupClickHandlers();
});

function handleAjaxStartAndStop() {
  $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
}

function initializeDataTable() {
  var true_icon = '<i class="material-icons" style="color: green">check</i>';
  var false_icon = '<i class="material-icons" style="color: red">close</i>';

  var candidate_urls_table = $("#candidate_urls_table").DataTable({
    scrollY: true,
    lengthMenu: [25, 50, 100, 500],
    pageLength: 100,
    serverSide: true,
    stateSave: true,
    searchDelay: 1000,
    orderCellsTop: true,
    pagingType: "input",
    dom: "lBfritip",
    buttons: [
      "spacer",
      "csv",
      "spacer",
      "createState",
      "savedStates",
      "spacer",
      "selectAll",
      "selectNone",
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
    columns: [
      getURLColumn(),
      getExcludedColumn(true_icon, false_icon),
      getScrapedTitleColumn(),
      getGeneratedTitleColumn(),
      getVisitedColumn(true_icon, false_icon),
      getDocumentTypeColumn(),
      { data: "id", visible: false, searchable: false },
      { data: "generated_title_id", visible: false, searchable: false },
      { data: "match_pattern_type", visible: false, searchable: false },
      { data: "candidate_urls_count", visible: false, searchable: false },
    ],
    createdRow: function (row, data, dataIndex) {
      if (data["excluded"]) {
        $(row).addClass("table-danger");
      }
    },
  });

  $("#excludedFilter").on("change", function () {
    console.log("working");
    $("#candidate_urls_table").DataTable().ajax.reload(null, false);
  });

  $("#candidateUrlFilter").on("keyup", function () {
    candidate_urls_table.columns(0).search(this.value).draw();
  });

  $("#candidateScrapedTitleFilter").on("keyup", function () {
    candidate_urls_table.columns(2).search(this.value).draw();
  });

  $("#candidateNewTitleFilter").on("keyup", function () {
    candidate_urls_table.columns(3).search(this.value).draw();
  });

  var exclude_patterns_table = $("#exclude_patterns_table").DataTable({
    scrollY: true,
    serverSide: true,
    orderCellsTop: true,
    lengthMenu: [25, 50, 100, 500],
    pageLength: 100,
    ajax: `/api/exclude-patterns/?format=datatables&collection_id=${collection_id}`,
    columns: [
      { data: "match_pattern" },
      {
        data: "match_pattern_type_display",
        class: "text-center",
        sortable: false,
      },
      { data: "reason", class: "text-center", sortable: false },
      { data: "candidate_urls_count", class: "text-center", sortable: false },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-exclude-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
    ],
  });

  $("#candidateMatchPatternFilter").on("keyup", function () {
    exclude_patterns_table.columns(0).search(this.value).draw();
  });

  $("#candidateReasonFilter").on("keyup", function () {
    exclude_patterns_table.columns(2).search(this.value).draw();
  });

  var include_patterns_table = $("#include_patterns_table").DataTable({
    scrollY: true,
    serverSide: true,
    orderCellsTop: true,
    lengthMenu: [25, 50, 100, 500],
    pageLength: 100,
    ajax: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
    columns: [
      { data: "match_pattern" },
      {
        data: "match_pattern_type_display",
        class: "text-center",
        sortable: false,
      },
      { data: "candidate_urls_count", class: "text-center", sortable: false },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-include-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
    ],
  });

  $("#candidateIncludeMatchPatternFilter").on("keyup", function () {
    include_patterns_table.columns(0).search(this.value).draw();
  });

  var title_patterns_table = $("#title_patterns_table").DataTable({
    scrollY: true,
    serverSide: true,
    orderCellsTop: true,
    lengthMenu: [25, 50, 100, 500],
    pageLength: 100,


    ajax: {url: `/api/title-patterns/?format=datatables&collection_id=${collection_id}`,
  
    success: function (data) {
      console.log("sdfad");
      console.log(data);

      setTimeout(() => {

        $(".testing").each(function (i) {
          console.log("inside");
          var table = $("#title_patterns_table").DataTable();
          console.log(title_patterns_table);
          var select = $(
            '<select><option value="' +
              table.column(i).header().innerText +
              '">' +
              table.column(i).header().innerText +
              "</option></select>"
          )
            .appendTo($(this).empty())
            .on("change", function () {
              table.column(i).search($(this).val()).draw();
            });
      
        
          // console.log("results", results);
          table
            .column(i)
            .data()
            .unique()
            .sort()
            .each(function (d, j) {
              console.log("D", d);
              select.append('<option value="' + d + '">' + d + "</option>");
            });
        });


      },5000);
      //await or sleep

     


    }
  
  },
    columns: [
      { data: "match_pattern" },
      {
        data: "match_pattern_type_display",
        class: "text-center",
        sortable: false,
      },
      { data: "title_pattern" },
      { data: "candidate_urls_count", class: "text-center", sortable: false },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-title-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
    ],
  });

  $("#candidateTitleMatchPatternFilter").on("keyup", function () {
    title_patterns_table.columns(0).search(this.value).draw();
  });

  var document_type_patterns_table = $(
    "#document_type_patterns_table"
  ).DataTable({
    scrollY: true,
    serverSide: true,
    orderCellsTop: true,
    lengthMenu: [25, 50, 100, 500],
    pageLength: 100,
    ajax: `/api/document-type-patterns/?format=datatables&collection_id=${collection_id}`,
    columns: [
      { data: "match_pattern" },
      {
        data: "match_pattern_type_display",
        class: "text-center",
        sortable: false,
      },
      { data: "document_type_display" },
      { data: "candidate_urls_count", class: "text-center", sortable: false },
      {
        data: null,
        sortable: false,
        class: "text-center",
        render: function (data, type, row) {
          return `<button class="btn btn-danger btn-sm delete-document-type-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
        },
      },
      { data: "id", visible: false, searchable: false },
    ],
  });

  $("#candidateDocTypeMatchPatternFilter").on("keyup", function () {
    document_type_patterns_table.columns(0).search(this.value).draw();
  });
}

function setupClickHandlers() {
  handleAddNewPatternClick();

  handleCreateDocumentTypePatternButton();
  handleCreateExcludePatternButton();
  handleCreateIncludePatternButton();
  handleCreateTitlePatternButton();

  handleDeleteDocumentTypeButtonClick();
  handleDeleteExcludePatternButtonClick();
  handleDeleteIncludePatternButtonClick();
  handleDeleteTitlePatternButtonClick();

  handleDocumentTypeSelect();
  handleExcludeIndividualUrlClick();
  handleNewTitleChange();

  handleUrlLinkClick();
}

function getURLColumn() {
  return {
    data: "url",
    render: function (data, type, row) {
      return `<a target="_blank" href="${data}" data-url="/api/candidate-urls/${
        row["id"]
      }/" class="url_link"> <i class="material-icons">open_in_new</i></a> <span class="candidate_url">${remove_protocol(
        data
      )}</span>`;
    },
  };
}

function getScrapedTitleColumn() {
  return {
    data: "scraped_title",
  };
}

function getGeneratedTitleColumn() {
  return {
    data: "generated_title",
    render: function (data, type, row) {
      return `<input type="text" class="form-control individual_title_input" value='${data}' data-generated-title-id=${
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

function getVisitedColumn(true_icon, false_icon) {
  true_icon =
    '<i class="material-icons visited_icon" style="color: green">check</i>';
  false_icon =
    '<i class="material-icons visited_icon" style="color: red">close</i>';
  return {
    data: "visited",
    class: "col-1 text-center",
    render: function (data, type, row) {
      return data === true ? true_icon : false_icon;
    },
  };
}

// function getExcludedColumnTest() {
//   return {
//     data: "excluded",
//     class: "col-1 text-center",

//     render: function (data, type, row) {
//       var dict = {
//         1: "Yes",
//         2: "No",
//       };
//       button_color = data ? "btn-success" : "btn-secondary";
//       button_text = data ? dict[data] : "Exclude";

//       return `
//           <div class="dropdown document_type_dropdown" data-match-pattern=${remove_protocol(
//             row["url"]
//           )}>
//             <button class="btn ${button_color} btn-sm dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
//               ${button_text}
//             </button>
//             <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
//               <a class="dropdown-item document_type_select" href="#" value="1">Yes</a>
//               <a class="dropdown-item document_type_select" href="#" value="2">No</a>
//             </div>
//           </div>`;
//     },
//   };
// }

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
            <div class="dropdown document_type_dropdown" data-match-pattern=${remove_protocol(
              row["url"]
            )}>
              <button class="btn ${button_color} btn-sm dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
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
function handleCreateDocumentTypePatternButton() {
  $("body").on("click", ".create_document_type_pattern_button", function () {
    $modal = $("#documentTypePatternModal").modal();
  });
}

function handleCreateExcludePatternButton() {
  $("body").on("click", ".create_exclude_pattern_button", function () {
    $modal = $("#excludePatternModal").modal();
  });
}

function handleCreateIncludePatternButton() {
  $("body").on("click", ".create_include_pattern_button", function () {
    $modal = $("#includePatternModal").modal();
  });
}

function handleCreateTitlePatternButton() {
  $("body").on("click", ".create_title_pattern_button", function () {
    $modal = $("#titlePatternModal").modal();
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
      (match_pattern_type = 1)
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
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function postExcludePatterns(match_pattern, match_pattern_type = 0) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to exclude.");
    return;
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
  }

  // Hide it AFTER the action was triggered
  $(".custom-menu").hide(100);
});

$("#exclude_pattern_form").on("submit", function (e) {
  e.preventDefault();
  inputs = {};
  input_serialized = $(this).serializeArray();
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
  inputs = {};
  input_serialized = $(this).serializeArray();
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

$("#filter-checkbox").on("change", function () {
  $("#candidate_urls_table").DataTable().ajax.reload(null, false);
});

$(document).ready(function () {
  $(".testing").each(function (i) {
    var table = $("#title_patterns_table").DataTable();
    var select = $(
      '<select><option value="' +
        table.column(i).header().innerText +
        '">' +
        table.column(i).header().innerText +
        "</option></select>"
    )
      .appendTo($(this).empty())
      .on("change", function () {
        table.column(i).search($(this).val()).draw();
      });

  
    // console.log("results", results);
    table
      .column(i)
      .data()
      .unique()
      .sort()
      .each(function (d, j) {
        console.log("D", d);
        select.append('<option value="' + d + '">' + d + "</option>");
      });
  });
});
