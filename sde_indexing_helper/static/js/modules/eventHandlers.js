export const eventHandlers = {
  setupHandlers: function() {
    // this.handleTabsClick();

    this.handleHideorShowSubmitButton();
    this.handleHideorShowKeypress();
    this.handleAddNewPatternClick();

    this.handleDeleteDocumentTypeButtonClick();
    this.handleDeleteExcludePatternButtonClick();
    this.handleDeleteIncludePatternButtonClick();
    this.handleDeleteTitlePatternButtonClick();
    this.handleDeleteDivisionButtonClick();

    this.handleDocumentTypeSelect();
    this.handleDivisionSelect();
    this.handleExcludeIndividualUrlClick();
    this.handleNewTitleChange();

    this.handleUrlLinkClick();
    this.handleTabsClick();

    this.handleWorkflowStatusSelect();

    // this.handleModals();
    // this.handlePatternActions();
    // this.handleTableFilters();
    // this.handleContextMenu();
  },

  handleHideorShowSubmitButton: function() {
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
  },

    handleHideorShowKeypress: function() {

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
  addEnterEscapeKeypress("#excludePatternModal", "#exclude_pattern_form");
  addEnterEscapeKeypress("#includePatternModal", "#include_pattern_form");
  addEnterEscapeKeypress("#titlePatternModal", "#title_pattern_form");
  addEnterEscapeKeypress("#documentTypePatternModal", "#document_type_pattern_form");
  addEnterEscapeKeypress("#divisionPatternModal", "#division_pattern_form");
},

    handleDeleteDocumentTypeButtonClick: function() {
        $("body").on("click", ".delete-document-type-pattern-button", function () {
            patternRowId = $(this).data("row-id");
            currentURLtoDelete = `/api/document-type-patterns/${patternRowId}/`;
            deletePattern(
              `/api/document-type-patterns/${patternRowId}/`,
              (data_type = "Document Type Pattern")
            );
          });
        },

    handleDeleteExcludePatternButtonClick: function() {
        $("body").on("click", ".delete-exclude-pattern-button", function () {
            var patternRowId = $(this).data("row-id");
            currentURLtoDelete = `/api/exclude-patterns/${patternRowId}/`;
            deletePattern(
              `/api/exclude-patterns/${patternRowId}/`,
              (data_type = "Exclude Pattern")
            );
          });
        },

    handleDeleteIncludePatternButtonClick: function() {
        ("body").on("click", ".delete-include-pattern-button", function () {
            var patternRowId = $(this).data("row-id");
            currentURLtoDelete = `/api/include-patterns/${patternRowId}/`;
            deletePattern(
              `/api/include-patterns/${patternRowId}/`,
              (data_type = "Include Pattern")
            );
          });
        },

    handleDeleteTitlePatternButtonClick: function() {
        $("body").on("click", ".delete-title-pattern-button", function () {
            var patternRowId = $(this).data("row-id");
            currentURLtoDelete = `/api/title-patterns/${patternRowId}/`;
            deletePattern(
              `/api/title-patterns/${patternRowId}/`,
              (data_type = "Title Pattern")
            );
          });
        },

    handleDeleteDivisionButtonClick: function() {
        $("body").on("click", ".delete-division-pattern-button", function () {
            var patternRowId = $(this).data("row-id");
            currentURLtoDelete = `/api/division-patterns/${patternRowId}/`;
            deletePattern(
                `/api/division-patterns/${patternRowId}/`,
                "Division Pattern"
            );
            });
        },

    handleAddNewPatternClick: function() {
        $("body").on("click", ".add_new_pattern", function () {
            var pattern = $(this).parents(".pattern_row").find("input").val();
            postExcludePatterns(pattern);
            });
        },

    handleDocumentTypeSelect: function() {
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
        },

    handleDivisionSelect: function() {
        $("body").on("click", ".division_select", function () {
            var match_pattern = $(this).closest(".document_type_dropdown").data("match-pattern");
            var division = $(this).attr("value");
            postDivisionPatterns(match_pattern, 1, division);
          });
        },

    handleExcludeIndividualUrlClick: function() {
        $("body").on("click", ".exclude_individual_url", function () {
            postExcludePatterns(
              (match_pattern = $(this).attr("value")),
              (match_pattern_type = 1),
              true
            );
          });
        },

    handleNewTitleChange: function() {
        $("body").on("change", ".individual_title_input", function () {
            var match_pattern = $(this).data("url");
            var title_pattern = $(this).val();
            var generated_title_id = $(this).data("generated-title-id");
            var match_pattern_type = $(this).data("match-pattern-type");
            var delta_urls_count = $(this).data("delta-urls-count");
            if (!title_pattern) {
              currentURLtoDelete = `/api/title-patterns/${generated_title_id}/`;
              deletePattern(
                `/api/title-patterns/${generated_title_id}/`,
                (data_type = "Title Pattern"),
                (url_type = match_pattern_type),
                (delta_urls_count = delta_urls_count)
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
        },

    handleUrlLinkClick: function() {
        $("body").on("click", ".url_link", function (event) {
            var url = $(this).attr("data-url");
            postVisited(url);
            $(this)
              .closest("tr")
              .find(".visited_icon")
              .css("color", "green")
              .text("done");
          });
        },

    handleTabsClick: function() {
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
        $("#divisionPatternsTab").on("click", function () {
            newDivisionPatternsCount = 0;
            $("#divisionPatternsTab").html(`Division Patterns`);
        });
        },

    handleWorkflowStatusSelect: function() {
        $("body").on("click", ".workflow_status_select", function () {
            $("#workflowStatusChangeModal").modal();
            var collectionName = $(".urlStyle").text();
            var collection_id = $(this).data("collection-id");
            var workflow_status = $(this).attr("value");
            var new_workflow_status = $(this).text();

            $(".workflow-status-change-caption").html(
              `<div>Workflow status for <b class="bold">${collectionName}</b> will change to <b class="bold">${new_workflow_status}</b></div>`
            );
            $("#workflowStatusChangeModalForm").on("click", "button", function (event) {
              event.preventDefault();
              var buttonId = $(this).attr("id");

              switch (buttonId) {
                case "cancelworkflowStatusChange":
                  $("#workflowStatusChangeModal").modal("hide");
                  break;
                case "changeWorkflowStatus":
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

                  $button.text(new_workflow_status);
                  $button.removeClass(
                    "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
                  );
                  $button.addClass(color_choices[parseInt(workflow_status)]);
                  postWorkflowStatus(collection_id, workflow_status);
                  $("#workflowStatusChangeModal").modal("hide");
                  break;
              }
            });
          });
        }

//   handleModals: function() {
//     // ... modal handlers
//   },

//   handlePatternActions: function() {
//     // ... pattern action handlers
//   },

//   handleTableFilters: function() {
//     // ... table filter handlers
//   },

//   handleContextMenu: function() {
//     // ... context menu handlers
//   }
};
