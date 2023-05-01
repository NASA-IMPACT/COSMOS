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
    add_exclude_pattern($(this).attr("value"));
    $(this).removeClass('btn-success');
    $(this).addClass('btn-danger');
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
