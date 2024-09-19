var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;
collection_id = getCollectionId();

// Maybe you need to define a new DataTable for this page as well 
// So that you can refresh it any way you want 
// Or maybe this is not necessary

$(document).ready(function () {
    // handleAjaxStartAndStop();
    initializeDataTable();
    setupClickHandlers();
  });

function initializeDataTable() {
  var affected_urls_table = $("#urlsTable").DataTable({
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
      rowId: "url"
  }
  })
}

function setupClickHandlers() {
    handleIncludeIndividualUrlClick();
  }

function handleIncludeIndividualUrlClick() {
    $("body").on("click", ".include-url-btn", function () {

    const span = this.querySelector('span');
    if (span.classList.contains('cross-mark')) {
        // Change to tick mark
        span.classList.remove('cross-mark');
        span.innerHTML = '&#10004;';  // Tick mark
        // then add that URL to the includeURLs list
        match_pattern = remove_protocol($(this).attr("value")) ;
        match_pattern_type = INDIVIDUAL_URL;
        console.log(match_pattern);
        postIncludePatterns(
            match_pattern = match_pattern,
            match_pattern_type = match_pattern_type,
            true
          );
        
        const row = $(this).closest('tr'); // Get the closest table row
        const rowId = $("#urlsTable").DataTable().row(row).index();
        console.log(rowId);
        deleteRowById(rowId);

        //Along with this, remove this pattern from the exclude_patterns
        // First, check if similar kind of pattern is available in the exclude_pattern table
        // If yes, this run this block of code.
        // postExcludePatterns(
        //     match_pattern = match_pattern,
        //     match_pattern_type = match_pattern_type,
        //     true
        //   );

      
    } else {
        // Change back to cross mark
        span.classList.add('cross-mark');
        span.innerHTML = '&#10060;';  // Cross mark
    }

    });
  }

  function handleExcludeIndividualUrlClick() {
    // exclude that URL
    // check in the include patterns if similar URL is present
    // if yes then delete that URL in the 

  }

function postIncludePatterns(match_pattern, match_pattern_type = 0) {
  if (!match_pattern) {
    toastr.error("Please highlight a pattern to include.");
    return;
  }

  // if pattern exists in table already
  // var table = $("#include_patterns_table").DataTable();
  // var itemIdColumnData = table.column(0).data().toArray();
  // if (itemIdColumnData.includes(match_pattern)) {
  //   toastr.success("Pattern already exists");
  //   return;
  // }

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
      console.log("Success on adding to the Included URLs");
  //     $("#candidate_urls_table").DataTable().ajax.reload(null, false);
  //     $("#include_patterns_table").DataTable().ajax.reload(null, false);
  //     if(currentTab === ""){ //Only add a notification if we are on the first tab
  //     newIncludePatternsCount = newIncludePatternsCount + 1;
  //     $("#includePatternsTab").html(
  //       `Include Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
  //         newIncludePatternsCount + " new" +
  //         `</span>`
  //     );
  //   }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function getCollectionId() {
  return collection_id;
}

function remove_protocol(url) {
    return url.replace(/(^\w+:|^)\/\//, "");
  }


function postExcludePatterns(match_pattern, match_pattern_type = 0, force) {
//   if (!match_pattern) {
//     toastr.error("Please highlight a pattern to exclude.");
//     return;
//   }
//   if (!force) {
//     //If the user clicked the icon in the table, we make the change regardless
//     // if pattern exists in table already (unless another pattern overrules it)
//     var table = $("#exclude_patterns_table").DataTable();
//     var itemIdColumnData = table.column(0).data().toArray();
//     if (itemIdColumnData.includes(match_pattern)) {
//       toastr.success("Pattern already exists");
//       return;
//     }
//   }

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
    console.log("Success on removing from Excluded URLs");
    //   $("#candidate_urls_table").DataTable().ajax.reload(null, false);
    //   $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
    //   if(currentTab === ""){ //Only add a notification if we are on the first tab
    //   newExcludePatternsCount = newExcludePatternsCount + 1;
    //   $("#excludePatternsTab").html(
    //     `Exclude Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
    //       newExcludePatternsCount + " new" +
    //       `</span>`
    //   );
    // }
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
  });
}

function deleteRowById(rowId) {
    // Find the DataTable instance
    var affected_urls_table = $("#urlsTable").DataTable();
  
    // Find the row with ID 1
    var rowToDelete = affected_urls_table.row(rowId); // Adjust based on 0-indexing
  
    if (rowToDelete.length) {
      rowToDelete.remove(); // Remove the row
      affected_urls_table.draw(); // Redraw the table
    } else {
      console.log("Row not found.");
    }
  }
  