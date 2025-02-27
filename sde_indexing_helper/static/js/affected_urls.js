var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;

$(document).ready(function () {
  handleAjaxStartAndStop();
  initializeDataTable();
});

function handleAjaxStartAndStop() {
  $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
}

function initializeDataTable() {
  const PATTERN_ENDPOINTS = {
    Exclude: "exclude-pattern-affected-urls",
    Include: "include-pattern-affected-urls",
    Title: "title-pattern-affected-urls",
    "Document Type": "documenttype-pattern-affected-urls",
  };

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
      url: `/api/${PATTERN_ENDPOINTS[patternType]}/?format=datatables&url_type=${urlType}&pattern_id=${pattern_id}`,
      data: function (d) {},
      complete: function (xhr, status) {},
    },

    columns: [
      { data: "id", class: "whiteText text-center" },
      getURLColumn(),
    ],
  });

  $("#affectedURLsFilter").on(
    "beforeinput",
    DataTable.util.debounce(function (val) {
      affected_urls_table.columns(0).search(this.value).draw();
    }, 1000)
  );
}

function getURLColumn() {
  return {
    data: "url",
    width: "30%",
    render: function (data, type, row) {
      return `<div class="url-cell"><span class="candidate_url nameStyling">${data}</span>
              <a target="_blank" href=${data} class="url-link">
              <i class="material-icons url-icon">open_in_new</i></a>
              </div>`;
    },
  };
}
