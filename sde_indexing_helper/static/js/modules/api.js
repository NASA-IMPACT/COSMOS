export const api = {
  postExcludePatterns: function(match_pattern, match_pattern_type = 0, force) {
    if (!match_pattern) {
      toastr.error("Please highlight a pattern to exclude.");
      return;
    }
    if (!force) {
      //If the user clicked the icon in the table, we make the change regardless
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
        $("#delta_urls_table").DataTable().ajax.reload(null, false);
        $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
        if (currentTab === "") { //Only add a notification if we are on the first tab
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
  },

  postIncludePatterns: function(match_pattern, match_pattern_type = 0) {
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
        $("#delta_urls_table").DataTable().ajax.reload(null, false);
        $("#include_patterns_table").DataTable().ajax.reload(null, false);
        if (currentTab === "") { //Only add a notification if we are on the first tab
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
  },

  postTitlePatterns: function(match_pattern, title_pattern, match_pattern_type = 1) {
    if (!match_pattern) {
        toastr.error("Please highlight a pattern to change the title.");
        return;
      }

      $.ajax({
        url: '/api/title-patterns/',
        type: "POST",
        data: {
          collection: collection_id,
          match_pattern: match_pattern,
          match_pattern_type: match_pattern_type,
          title_pattern: title_pattern,
          csrfmiddlewaretoken: csrftoken
        },
        success: function (data) {
          $('#delta_urls_table').DataTable().ajax.reload(null, false);
          $('#title_patterns_table').DataTable().ajax.reload(null, false);
          if (currentTab === "") { //Only add a notification if we are on the first tab
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
          if (errorMessage == '{"error":{"non_field_errors":["The fields collection, match_pattern must make a unique set."]},"status_code":400}') {
            toastr.success("Pattern already exists");
            return;
          }
          var errorMessages = JSON.parse(errorMessage);
          Object.entries(errorMessages.error).forEach(([key, value]) => {
            toastr.error(value, key);
          });
        }
      });
  },

  postDocumentTypePatterns: function(match_pattern, match_pattern_type, document_type) {
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
          $("#delta_urls_table").DataTable().ajax.reload(null, false);
          $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
          if (currentTab === "") { //Only add a notification if we are on the first tab
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
          if (
            errorMessage ==
            '{"error":{"non_field_errors":["The fields collection, match_pattern must make a unique set."]},"status_code":400}'
          ) {
            toastr.success("Pattern already exists");
            return;
          }
          toastr.error(errorMessage);
        },
      });
  },

  postDivisionPatterns: function(match_pattern, match_pattern_type, division) {
    if (!match_pattern) {
        toastr.error("Please highlight a pattern to add division.");
        return;
      }

      $.ajax({
        url: "/api/division-patterns/",
        type: "POST",
        data: {
          collection: collection_id,
          match_pattern: match_pattern,
          match_pattern_type: match_pattern_type,
          division: division,
          csrfmiddlewaretoken: csrftoken,
        },
        success: function (data) {
          $("#delta_urls_table").DataTable().ajax.reload(null, false);
          $("#division_patterns_table").DataTable().ajax.reload(null, false);
          if (currentTab === "") { // Only add a notification if we are on the first tab
            newDivisionPatternsCount = newDivisionPatternsCount + 1;
            $("#divisionPatternsTab").html(
              `Division Patterns <span class="pill notifyBadge badge badge-pill badge-primary">` +
              newDivisionPatternsCount + " new" +
              `</span>`
            );
          }
        },
        error: function (xhr, status, error) {
          var errorMessage = xhr.responseText;
          if (
            errorMessage ==
            '{"error":{"non_field_errors":["The fields collection, match_pattern must make a unique set."]},"status_code":400}'
          ) {
            toastr.success("Pattern already exists");
            return;
          }
          toastr.error(errorMessage);
        },
      });
  },

  postWorkflowStatus: function(collection_id, workflow_status) {
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
  },

  deletePattern: function(url, data_type, url_type = null, delta_urls_count = null) {
    if (url_type === MULTI_URL_PATTERN) {
        var confirmDelete = confirm(
          `YOU ARE ATTEMPTING TO DELETE A MULTI-URL PATTERN. THIS WILL AFFECT ${delta_urls_count} URLs. \n\nAre you sure you want to do this? Currently there is no way to delete a single URL from a Multi-URL pattern`
        );
      } else {
        $modal = $("#deletePatternModal").modal({
          backdrop: "static",
          keyboard: true,
        });

        $(".delete-pattern-caption").text(
          `Are you sure you want to delete this ${data_type}?`
        );
      }

      $("#deletePatternModal").on("keydown", function (event) {
        if (event.keyCode === 13) {
          // Check if the focused element is the button
          if (
            document.activeElement.id === "deletePatternModal" &&
            url === currentURLtoDelete
          ) {
            // Simulate a click event on the button
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
                $modal = $("#deletePatternModal").modal("hide");
                $("#delta_urls_table").DataTable().ajax.reload(null, false);
                $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
                $("#include_patterns_table").DataTable().ajax.reload(null, false);
                $("#title_patterns_table").DataTable().ajax.reload(null, false);
                $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
                $("#division_patterns_table").DataTable().ajax.reload(null, false);
              },
            });
          }
        }
      });

      $("#deletePatternModalForm").on("click", "button", function (event) {
        event.preventDefault();
        var buttonId = $(this).attr("id");
        if (buttonId === "dontDeletePattern") {
          $modal = $("#deletePatternModal").modal("hide");
          return;
        } else if (buttonId === "deletePattern" && url === currentURLtoDelete) {
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
              $("#delta_urls_table").DataTable().ajax.reload(null, false);
              $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
              $("#include_patterns_table").DataTable().ajax.reload(null, false);
              $("#title_patterns_table").DataTable().ajax.reload(null, false);
              $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
              $("#division_patterns_table").DataTable().ajax.reload(null, false);
            },
          });
        }
      });

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
          $("#delta_urls_table").DataTable().ajax.reload(null, false);
          $("#exclude_patterns_table").DataTable().ajax.reload(null, false);
          $("#include_patterns_table").DataTable().ajax.reload(null, false);
          $("#title_patterns_table").DataTable().ajax.reload(null, false);
          $("#document_type_patterns_table").DataTable().ajax.reload(null, false);
          $("#division_patterns_table").DataTable().ajax.reload(null, false);
        },
      });
  }
};
