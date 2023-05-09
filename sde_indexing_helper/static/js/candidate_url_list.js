$(document).ready(function () {
    // Get the value of the "param" GET parameter from the URL
    var paramValue = getParameterByName("is_excluded");

    // If the "param" GET parameter exists and its value is "true"
    if (paramValue === "false") {
        // Check the checkbox with ID "myCheckbox"
        $("#excluded_bool").prop("checked", true);
    }
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

// Function to get the value of a GET parameter by its name
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

$("#excluded_bool").on("click", function () {
    if ($(this).prop("checked")) {
        // Get the current URL
        var url = window.location.href;

        // Add a GET parameter
        var newUrl = url + "?is_excluded=false";

        // Redirect to the new URL
        window.location.href = newUrl;
    } else {
        // Get the current URL
        var url = window.location.href;

        // Remove all GET parameters
        var newUrl = url.split("?")[0];

        // Redirect to the new URL
        window.location.href = newUrl;
    };
});



$("#excluded_bool").on("click", function () {
    if ($(this).prop("checked")) {
        $("#excluded").val("True");
    } else {
        $("#excluded").val("False");
    };
});

$("#visited_bool").on("click", function () {
    if ($(this).prop("checked")) {
        $("#visited").val("True");
    } else {
        $("#visited").val("False");
    };
});

$(".url_part_button").on("click", function () {
    $.post('/api/exclude-patterns/', {
        collection: '85',
        match_pattern: $(this).attr("value"),
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        console.log(response);
        window.location.reload();
    });
});

function add_exclude_pattern(pattern) {
    let input = $(
        `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" value="${pattern}*" />
                </div>
                <div class="col">
                    <button type="button" class="btn btn-danger btn-sm delete_input" hx-delete="/exclude-pattern" hx-confirm="Are you sure you wish to delete this pattern?">x</button>
                </div>
            </div>
        `
    );
    $('#exclude_patterns').append(input);
}

$('#add_exclude_pattern').on('click', function () {
    let input = $(
        `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" />
                </div>
                <div class="col">
                    <button type="button" class="btn btn-danger btn-sm delete_input">
                        x
                    </button>
                </div>
            </div>
        `
    );
    $('#exclude_patterns').append(input);
});

$("body").on("click", ".delete_input", function () {
    $(this).parents(".pattern_row").remove();
});

$(".new-title").on("change", function () {
    let title = $(this).val();
    let url = $(this).attr("data-url");
    $.ajax({
        url: url,
        type: "POST",
        data: {
            title: title,
            csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
        },
        success: function (data) {
            console.log(data);
        },
    });
});
