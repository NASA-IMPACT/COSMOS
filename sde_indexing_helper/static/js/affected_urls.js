var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;
collection_id = getCollectionId();

$(document).ready(function () {
  initializeDataTable();
});

function initializeDataTable() {
  var affected_urls_table = $("#affectedURLsTable").DataTable({
    pageLength: 100,
    colReorder: true,
    stateSave: true,
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
      },
      serverSide: true,
      orderCellsTop: true,
      pagingType: "input",
      rowId: "url",
    },
  });

  $("#affectedURLsFilter").on(
    "beforeinput",
    DataTable.util.debounce(function (val) {
      affected_urls_table.columns(1).search(this.value).draw();
    }, 1000)
  );
}
