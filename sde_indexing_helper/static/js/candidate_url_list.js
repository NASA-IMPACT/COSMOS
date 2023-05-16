// CSRF token and collection_id
var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var collection_id = getCollectionId();
var selected_text = "";

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

    var candidate_urls_table = $('#candidate_urls_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "ajax": {
            "url": `/api/candidate-urls/?format=datatables&collection_id=${collection_id}`,
            "data": function (d) {
                d.is_excluded = $('#filter-checkbox').is(':checked') ? false : null;
            }
        },
        "columns": [
            getURLColumn(),
            getExcludedColumn(true_icon, false_icon),
            getScrapedTitleColumn(),
            getGeneratedTitleColumn(),
            getVisitedColumn(true_icon, false_icon),
            { "data": "document_type", },
            { "data": "id", "visible": false, "searchable": false },
        ],
        "createdRow": function (row, data, dataIndex) {
            if (data['excluded']) {
                $(row).addClass('table-danger');
            }
        }
    });

    var exclude_patterns_table = $('#exclude_patterns_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "ajax": `/api/exclude-patterns/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            { "data": "match_pattern" },
            { "data": "match_pattern_type_display", "class": "text-center", "sortable": false },
            { "data": "reason", "class": "text-center", "sortable": false },
            { "data": "candidate_urls_count", "class": "text-center", "sortable": false },
            {
                "data": null,
                "sortable": false,
                "class": "text-center",
                "render": function (data, type, row) {
                    return `<button class="btn btn-danger btn-sm delete-exclude-pattern-button" data-row-id="${row['id']}"><i class="material-icons">delete</i></button >`;
                }
            },
            { "data": "id", "visible": false, "searchable": false },
        ]
    });

    var title_patterns_table = $('#title_patterns_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "ajax": `/api/title-patterns/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            { "data": "match_pattern" },
            { "data": "match_pattern_type_display", "class": "text-center", "sortable": false },
            { "data": "title_pattern" },
            { "data": "candidate_urls_count", "class": "text-center", "sortable": false },
            {
                "data": null,
                "sortable": false,
                "class": "text-center",
                "render": function (data, type, row) {
                    return `<button class="btn btn-danger btn-sm delete-title-pattern-button" data-row-id="${row['id']}"><i class="material-icons">delete</i></button >`;
                }
            },
            { "data": "id", "visible": false, "searchable": false },
        ]
    });

    var document_type_patterns_table = $('#document_type_patterns_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "ajax": `/api/document-type-patterns/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            { "data": "match_pattern" },
            { "data": "match_pattern_type_display", "class": "text-center", "sortable": false },
            { "data": "document_type" },
            { "data": "candidate_urls_count", "class": "text-center", "sortable": false },
            {
                "data": null,
                "sortable": false,
                "class": "text-center",
                "render": function (data, type, row) {
                    return `<button class="btn btn-danger btn-sm delete-title-pattern-button" data-row-id="${row['id']}"><i class="material-icons">delete</i></button >`;
                }
            },
            { "data": "id", "visible": false, "searchable": false },
        ]
    });
}

function setupClickHandlers() {
    handleUrlPartButton();
    handleExcludeIndividualUrlClick();
    handleDeleteExcludePatternButtonClick();
    handleDeleteTitlePatternButtonClick();
    handleAddNewPatternClick();
    handleNewTitleChange();
    handleUrlLinkClick();
}

function getURLColumn() {
    return {
        "data": "url", "render": function (data, type, row) {
            return `<a target="_blank" href="${data}" data-url="/api/candidate-urls/${row['id']}/" class="url_link"> <i class="material-icons">open_in_new</i></a> <span class="candidate_url">${remove_protocol(data)}</span>`;
        }
    }
}

function getScrapedTitleColumn() {
    return {
        "data": "scraped_title"
    }
}

function getGeneratedTitleColumn() {
    return {
        "data": "generated_title", "render": function (data, type, row) {
            return `<input type="text" class="form-control individual_title_input" value="${data}" data-url=${remove_protocol(row['url'])} />`;
        }
    }
}


function getExcludedColumn(true_icon, false_icon) {
    return {
        "data": "excluded", "class": "col-1 text-center", "render": function (data, type, row) {
            return (data === true) ? true_icon : `<a href="#" class="exclude_individual_url" value=${remove_protocol(row['url'])}>${false_icon}</a>`;
        }
    }
}

function getVisitedColumn(true_icon, false_icon) {
    true_icon = '<i class="material-icons visited_icon" style="color: green">check</i>';
    false_icon = '<i class="material-icons visited_icon" style="color: red">close</i>';
    return {
        "data": "visited", "class": "col-1 text-center", "render": function (data, type, row) {
            return (data === true) ? true_icon : false_icon;
        }
    }
}

function handleUrlPartButton() {
    $(".url_part_button").on("click", function () {
        postExcludePatterns($(this).attr("value"));
    });
}

function handleExcludeIndividualUrlClick() {
    $("body").on("click", '.exclude_individual_url', function () {
        postExcludePatterns(match_pattern = $(this).attr("value"), match_pattern_type = 1);
    });
}

function handleDeleteExcludePatternButtonClick() {
    $("body").on("click", ".delete-exclude-pattern-button", function () {
        row_id = $(this).data('row-id');
        deletePattern(`/api/exclude-patterns/${row_id}/`, data_type = 'Exclude Pattern');
    });
}

function handleDeleteTitlePatternButtonClick() {
    $("body").on("click", ".delete-title-pattern-button", function () {
        row_id = $(this).data('row-id');
        deletePattern(`/api/title-patterns/${row_id}/`, data_type = 'Title Pattern');
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
        var match_pattern = $(this).data('url');
        var title_pattern = $(this).val();
        postTitlePatterns(match_pattern, title_pattern, match_pattern_type = 1, title_pattern_type = 1);
    });
}

function handleUrlLinkClick() {
    $("body").on("click", ".url_link", function (event) {
        var url = $(this).attr("data-url");
        postVisited(url);
        $(this).closest('tr').find('.visited_icon').css('color', 'green').text('done');
    });
}

function postExcludePatterns(match_pattern, match_pattern_type = 0) {
    if (!match_pattern) {
        toastr.error('Please highlight a pattern to exclude.');
        return;
    }

    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: match_pattern,
        match_pattern_type: match_pattern_type,
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        $('#candidate_urls_table').DataTable().ajax.reload();
        $('#exclude_patterns_table').DataTable().ajax.reload();
    });
}

function postTitlePatterns(match_pattern, title_pattern, match_pattern_type = 1) {
    if (!match_pattern) {
        toastr.error('Please highlight a pattern to change the title.');
        return;
    }

    if (!title_pattern) {
        toastr.error('Please enter a title pattern.');
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
            $('#candidate_urls_table').DataTable().ajax.reload();
            $('#title_patterns_table').DataTable().ajax.reload();
        },
        error: function (xhr, status, error) {
            var errorMessage = xhr.responseText;
            toastr.error(errorMessage);
        }
    });
}

function postVisited(url) {
    $.ajax({
        url: url,
        type: "PUT",
        data: {
            visited: true,
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
        },
    });
}

function deletePattern(url, data_type) {
    var confirmDelete = confirm(`Are you sure you want to delete this ${data_type}?`);
    if (!confirmDelete) {
        return;
    }
    $.ajax({
        url: url,
        type: "DELETE",
        data: {
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
            $('#candidate_urls_table').DataTable().ajax.reload();
            $('#exclude_patterns_table').DataTable().ajax.reload();
            $('#title_patterns_table').DataTable().ajax.reload();
        }
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
    return url.replace(/(^\w+:|^)\/\//, '');
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
    $('#exclude_patterns').append(input);
}

// Trigger action when the contexmenu is about to be shown
$("body").on("contextmenu", ".candidate_url", function (event) {

    // Avoid the real one
    event.preventDefault();


    // Show contextmenu
    $(".custom-menu").finish().toggle(100).

        // In the right position (the mouse)
        css({
            top: event.pageY + "px",
            left: event.pageX - 250 + "px"
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
    // postTitlePatterns(match_pattern = selected_text.trim(), title_pattern = "hey", match_pattern_type = 2)
    // postTitlePatterns(match_pattern = selected_text.trim(), title_pattern = "hey", match_pattern_type = 2) // xpath
    $modal = $('#titlePatternModal').modal();
    $modal.find('#match_pattern_input').val(selected_text);
}

// If the menu element is clicked
$(".custom-menu li").click(function () {

    // This is the triggered action name
    switch ($(this).attr("data-action")) {
        case "exclude-pattern": postExcludePatterns(selected_text.trim(), match_pattern_type = 2); break;
        case "title-pattern": title_pattern_form(selected_text.trim()); break;
    }

    // Hide it AFTER the action was triggered
    $(".custom-menu").hide(100);
});

$('#title_pattern_form').on('submit', function (e) {
    e.preventDefault();
    inputs = {};
    input_serialized = $(this).serializeArray();
    input_serialized.forEach(field => {
        inputs[field.name] = field.value;
    });

    postTitlePatterns(match_pattern = inputs.match_pattern, title_pattern = inputs.title_pattern, match_pattern_type = 2);

    // close the modal if it is open
    $('#titlePatternModal').modal('hide');
});

$('#filter-checkbox').on('change', function () {
    $('#candidate_urls_table').DataTable().ajax.reload();
});
