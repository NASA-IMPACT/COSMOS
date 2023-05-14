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

    var table = $('#candidate_urls_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "stateSave": true,
        "ajax": `/api/candidate-urls/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            getURLColumn(),
            getExcludedColumn(true_icon, false_icon),
            getScrapedTitleColumn(),
            getGeneratedTitleColumn(),
            getVisitedColumn(true_icon, false_icon),
            { "data": "id", "visible": false, "searchable": false },
        ],
        "createdRow": function (row, data, dataIndex) {
            if (data['excluded']) {
                $(row).addClass('table-danger');
            }
        }
    });
}

function setupClickHandlers() {
    handleExcludedBool();
    handleVisitedBool();
    handleUrlPartButton();
    handleExcludeIndividualUrlClick();
    handleAddExcludePatternClick();
    handleDeleteInputClick();
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
            return `<input type="text" class="form-control individual_title_input" value="${data}" data-url=${row['url']} />`;
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

function handleExcludedBool() {
    $("#excluded_bool").on("click", function () {
        var newValue = $(this).prop("checked") ? "True" : "False";
        $("#excluded").val(newValue);
        updateUrlWithExclusion(newValue);
    });
}

function handleVisitedBool() {
    $("#visited_bool").on("click", function () {
        var newValue = $(this).prop("checked") ? "True" : "False";
        $("#visited").val(newValue);
    });
}

function handleUrlPartButton() {
    $(".url_part_button").on("click", function () {
        postExcludePatterns($(this).attr("value"));
    });
}

function handleExcludeIndividualUrlClick() {
    $("body").on("click", '.exclude_individual_url', function () {
        postExcludePatterns(match_pattern = $(this).attr("value"), pattern_type = 1);
    });
}

function handleAddExcludePatternClick() {
    $('#add_exclude_pattern').on('click', function () {
        add_exclude_pattern();
    });
}

function handleDeleteInputClick() {
    $("body").on("click", ".delete_input", function () {
        $(this).parents(".pattern_row").remove();
        window.location.reload();
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
        postIndividualTitle(match_pattern, title_pattern);
    });
}

function handleUrlLinkClick() {
    $("body").on("click", ".url_link", function (event) {
        var url = $(this).attr("data-url");
        postVisited(url);
        $(this).closest('tr').find('.visited_icon').css('color', 'green').text('done');
    });
}

function postExcludePatterns(match_pattern, pattern_type = 0) {
    if (!match_pattern) {
        toastr.error('Please highlight a pattern to exclude.');
        return;
    }

    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: match_pattern,
        pattern_type: pattern_type,
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        window.location.reload();
    });
}

function postIndividualTitle(match_pattern, title_pattern) {
    if (!match_pattern) {
        toastr.error('Please highlight a pattern to change the title.');
        return;
    }

    $.ajax({
        url: '/api/title-patterns/',
        type: "POST",
        data: {
            collection: collection_id,
            match_pattern: match_pattern,
            title_pattern: title_pattern,
            pattern_type: 1, // individual
            csrfmiddlewaretoken: csrftoken
        },
        success: function (data) {
            window.location.reload();
        },
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

// If the menu element is clicked
$(".custom-menu li").click(function () {

    // This is the triggered action name
    switch ($(this).attr("data-action")) {

        // A case for each action. Your actions here
        case "exclude-pattern": postExcludePatterns(selected_text.trim(), pattern_type = 2); break;
        case "title-pattern": alert("title"); break;
    }

    // Hide it AFTER the action was triggered
    $(".custom-menu").hide(100);
});
