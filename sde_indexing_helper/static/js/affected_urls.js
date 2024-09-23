var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;
collection_id = getCollectionId();

$(document).ready(function () {
    // handleAjaxStartAndStop();
    initializeDataTable();
    setupClickHandlers();
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
      rowId: "url"
  },
    // createdRow: function (row, data, dataIndex) {
    //     // Assuming the 'Include URL' column is at index 3
    //     let includeUrlCell = $(row).find('td').eq(2);

    //     // Check if the cell has the cross-mark
    //     if (includeUrlCell.find('i.cross-mark').length > 0) {
    //         // Highlight the row if it contains a cross-mark
    //         $(row).css('background-color', 'rgba(255, 61, 87, 0.36)'); // Light red background
    //     }
    // }

  })
}

function setupClickHandlers() {
    handleIncludeIndividualUrlClick();
  }

function handleIncludeIndividualUrlClick() {
    $("body").on("click", ".include-url-btn", function () {

    const i = this.querySelector('i');
    if (i.classList.contains('cross-mark')) {
        // Change to tick mark
        i.classList.remove('cross-mark');
        i.classList.add('tick-mark'); // Add the tick-mark class
        i.style.color = 'green'; // Change color to green
        i.textContent = 'check'; // Set the text to "check"
        let parentCol3 = i.closest('.col-3');
        // Change the data-sort attribute of the parent element
        if (parentCol3) {
            parentCol3.setAttribute('data-sort', '1'); // Set data-sort to '1' for the check-mark
        }

        // // Change to tick mark
        // i.classList.remove('cross-mark');
        // i.innerHTML = '&#10004;';  // Tick mark
        // then add that URL to the includeURLs list
        match_pattern = remove_protocol($(this).attr("value")) ;
        match_pattern_type = INDIVIDUAL_URL;
        console.log(match_pattern);
        postIncludePatterns(
            match_pattern = match_pattern,
            match_pattern_type = match_pattern_type,
            true
          );
        
        // const row = $(this).closest('tr'); // Get the closest table row
        // const rowId = $("#affectedURLsTable").DataTable().row(row).index();
        // console.log(rowId);
        // deleteRowById(rowId);

        //Along with this, remove this pattern from the exclude_patterns
        // First, check if similar kind of pattern is available in the exclude_pattern table
        // If yes, this run this block of code.
        // postExcludePatterns(
        //     match_pattern = match_pattern,
        //     match_pattern_type = match_pattern_type,
        //     true
        //   );

    
    } else {
        // Handle the functionality of excluding that URL again (maybe delete that include pattern which was just created)
        var url = $(this).attr("value");
        console.log("url", url);
        getCorrespondingIncludePattern(url).then(function(patternId) {
            if (patternId !== null) {
                console.log('Pattern ID:', patternId);
                currentURLtoDelete = `/api/include-patterns/${patternId}/`;
                deletePattern(
                  currentURLtoDelete,
                  (data_type = "Include Pattern")
                );
                
                // Change back to cross mark
                i.classList.remove('tick-mark');
                i.classList.add('cross-mark'); // Add the cross-mark class
                i.style.color = 'red'; // Change color to red
                i.textContent = 'close'; // Set the text to "close"
                let parentCol3 = i.closest('.col-3');
                // Change the data-sort attribute of the parent element
                if (parentCol3) {
                    parentCol3.setAttribute('data-sort', '0'); // Set data-sort to '0' for the cross-mark
                }


                console.log("URL removed from the include pattern")


            } else {
                console.log('No matching pattern found.');
            }
        }).catch(function(error) {
            console.error("Error occurred:", error);
        });
    
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
    var affected_urls_table = $("#affectedURLsTable").DataTable();
  
    // Find the row with ID 1
    var rowToDelete = affected_urls_table.row(rowId); // Adjust based on 0-indexing
  
    if (rowToDelete.length) {
      rowToDelete.remove(); // Remove the row
      affected_urls_table.draw(); // Redraw the table
    } else {
      console.log("Row not found.");
    }
  }

function deletePattern(
  url,
  data_type,
  url_type = null,
  candidate_urls_count = null
) {
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
          console.log("Successfully deleted.")
        },
      });
}

function getCorrespondingIncludePattern(url) {
    return $.ajax({
        url: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
        method: 'GET',
        dataType: 'json'
    }).then(function(response) {
        // Iterate through the 'data' array to find a matching pattern
        for (let i = 0; i < response.data.length; i++) {
            let pattern = response.data[i].match_pattern;
            if ( pattern === remove_protocol(url)) {
                return response.data[i].id; // Return the first matching pattern id
            }
        }
        return null; // Return null if no pattern matches
    }).catch(function(error) {
        console.error("Error fetching include patterns:", error);
        return null;
    });
}