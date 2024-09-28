var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var INDIVIDUAL_URL = 1;
var MULTI_URL_PATTERN = 2;
collection_id = getCollectionId();

$(document).ready(function () {
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
        buttons: [
          {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
              $modal = $("#includePatternModal").modal();
            },
          },
        ],
      },
      serverSide: true,
      orderCellsTop: true,
      pagingType: "input",
      rowId: "url",
    },
    columnDefs: [
      { orderable: true, targets: "_all" },
      { orderable: false, targets: "filter-row" },
    ],
    orderCellsTop: true,
  });

  $("#affectedURLsFilter").on(
    "beforeinput",
    DataTable.util.debounce(function (val) {
      affected_urls_table.columns(1).search(this.value).draw();
    }, 1000)
  );
}

// var pattern_type = "Exclude";
// function initializeDataTable() {
//   var affected_urls_table = $("#affectedURLsTable").DataTable({
//     pageLength: 100,
//     colReorder: true,
//     stateSave: true,
//     serverSide: true,
//     ajax: {
//       url: `/api/affected-urls/?format=datatables&collection_id=${collection_id}`,  // Replace with your actual API endpoint
//       data: function(d) {
//         d.pattern_type = pattern_type;  // Assuming pattern_type is defined globally
//       }
//     },
//     columns: [
//       { data: null, render: function (data, type, row, meta) {
//           return meta.row + meta.settings._iDisplayStart + 1;
//         }
//       },
//       { data: 'url', render: function(data, type, row) {
//           return '<div class="url-cell"><span class="candidate_url nameStyling">' + data + '</span>' +
//                  '<a target="_blank" href="' + data + '" data-url="/api/candidate-urls/' + row.id + '/" class="url-link">' +
//                  '<i class="material-icons url-icon">open_in_new</i></a></div>';
//         }
//       },
//       { data: 'included', render: function(data, type, row) {
//           if (pattern_type === "Exclude") {
//             var icon = data ? '<i class="material-icons tick-mark" style="color: green">check</i>' : '<i class="material-icons cross-mark" style="color: red">close</i>';
//             return '<a class="include-url-btn" data-url-id="' + row.id + '" value="' + row.url + '" included_by_pattern="' + row.included_by_pattern + '" match_pattern_id="' + row.match_pattern_id + '">' + icon + '</a>';
//           }
//           return '';
//         },
//         visible: pattern_type === "Exclude"
//       }
//     ],
//     layout: {
//       bottomEnd: "inputPaging",
//       topEnd: null,
//       topStart: {
//         info: true,
//         pageLength: {
//           menu: [
//             [25, 50, 100, 500],
//             ["Show 25", "Show 50", "Show 100", "Show 500"],
//           ],
//         },
//         buttons: [
//           {
//             text: "Add Pattern",
//             className: "addPattern",
//             action: function () {
//               $("#includePatternModal").modal('show');
//             },
//           },
//         ],
//       },
//     },
//     orderCellsTop: true,
//     pagingType: "input",
//     rowId: "url",
//     columnDefs: [
//       { orderable: true, targets: "_all" },
//       { orderable: false, targets: "filter-row" },
//     ],
//   });

//   $("#affectedURLsFilter").on(
//     "beforeinput",
//     DataTable.util.debounce(function (val) {
//       affected_urls_table.columns(1).search(this.value).draw();
//     }, 1000)
//   );
// }

function getCollectionId() {
  return collection_id;
}

function setupClickHandlers() {
  handleHideorShowSubmitButton();
  handleHideorShowKeypress();
  handleIncludeIndividualUrlClick();
}

function handleIncludeIndividualUrlClick() {
  var true_icon = '<i class="material-icons" style="color: green">check</i>';
  var false_icon = '<i class="material-icons" style="color: red">close</i>';

  $("#affectedURLsTable").on("click", ".include-url-btn", function () {
    const inclusion_status = this.querySelector("i");
    if (inclusion_status.classList.contains("cross-mark")) {
      // Change to tick mark
      // Also give this button the value of the include_pattern by which it was included.
      inclusion_status.classList.remove("cross-mark");
      inclusion_status.classList.add("tick-mark"); // Add the tick-mark class
      inclusion_status.style.color = "green"; // Change color to green
      inclusion_status.textContent = "check"; // Set the text to "check"
      let parentCol3 = inclusion_status.closest(".col-3");
      // Change the data-sort attribute of the parent element
      if (parentCol3) {
        parentCol3.setAttribute("data-sort", "1"); // Set data-sort to '1' for the check-mark
      }

      match_pattern = remove_protocol($(this).attr("value"));
      match_pattern_type = INDIVIDUAL_URL;
      console.log(match_pattern);

      postIncludePatterns(match_pattern, match_pattern_type)
        .then((result) => {
          console.log("New pattern ID:", result.id);
          console.log("Match pattern:", result.match_pattern);
          $(this).attr("included_by_pattern", result.match_pattern);
          $(this).attr("match_pattern_id", result.id);
        })
        .catch((error) => {
          console.error("Error:", error);
        });
    } else {
      var url = $(this).attr("value");
      var included_by_pattern = $(this).attr("included_by_pattern");
      var match_pattern_id = $(this).attr("match_pattern_id");

      console.log("url", url);
      console.log("included_by_pattern", included_by_pattern);
      console.log("match_pattern_id", match_pattern_id);

      if (included_by_pattern === remove_protocol(url)) {
        console.log(
          "Only this URL will be affected by this pattern: " + match_pattern_id
        );
        currentURLtoDelete = `/api/include-patterns/${match_pattern_id}/`;
        deletePattern(currentURLtoDelete, (data_type = "Include Pattern"));
        toastr.success("URL excluded successfully");
        // Change back to cross mark
        inclusion_status.classList.remove("tick-mark");
        inclusion_status.classList.add("cross-mark"); // Add the cross-mark class
        inclusion_status.style.color = "red"; // Change color to red
        inclusion_status.textContent = "close"; // Set the text to "close"
        let parentCol3 = inclusion_status.closest(".col-3");
        // Change the data-sort attribute of the parent element
        if (parentCol3) {
          parentCol3.setAttribute("data-sort", "0"); // Set data-sort to '0' for the cross-mark
        }
        // Also remove the included_by_pattern and match_pattern_id attributes
        $(this).attr("included_by_pattern", "None");
        $(this).attr("match_pattern_id", "None");
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
        console.log("Success on adding to the Included URLs");
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
      console.log("Successfully deleted.");
    },
    error: function (xhr, status, error) {
      var errorMessage = xhr.responseText;
      toastr.error(errorMessage);
    },
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
  console.log("input_serialized", input_serialized);
  $.ajax({
    url: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
    type: 'GET',
    success: function(response) {
      var existingPatterns = response.data.map(item => item.match_pattern);
      console.log("existingPatterns", existingPatterns);
      if (existingPatterns.includes(input_serialized[0].value)) {
        toastr.warning("Pattern already exists");
        $("#includePatternModal").modal("hide");
        return;
      }
      else {
        // if pattern does not exist, create a new pattern
        inputs = {};
        input_serialized.forEach((field) => {
          inputs[field.name] = field.value;
        });

        postIncludePatterns(
          (match_pattern = inputs.match_pattern),
          (match_pattern_type = 2)
        );
      }
    },
    error: function(xhr, status, error) {
      toastr.error("An error occurred while checking existing patterns");
    }
  });

  // close the modal if it is open
  $("#includePatternModal").modal("hide");
});

