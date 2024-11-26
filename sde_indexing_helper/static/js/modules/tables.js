export const initializeTables = {
    deltaUrls: function(collection_id) {
      return $('#delta_urls_table').DataTable({
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
                extend: "csv",
                exportOptions: {
                columns: [0, 11, 2, 12, 10],
                },
                customize: function (csv) {
                var lines = csv.split("\n");

                // Reorder the header columns
                var headers = lines[0].split(",");
                headers[4] = "New Title";
                var reorderedHeaders = [
                    headers[0],
                    headers[3],
                    headers[1],
                    headers[4],
                    headers[5],
                    headers[2],
                ];
                lines[0] = reorderedHeaders.join(",");

                const appliedFilt = [
                    [`URL:`, `${$("#deltaUrlFilter").val()}`.trim()],
                    [`Exclude:`, `${$(".dropdown-1").val()}`.trim()],
                    [
                    `Scraped Title:`,
                    `${$("#deltaScrapedTitleFilter").val()}`.trim(),
                    ],
                    [`New Title:`, `${$("#deltaNewTitleFilter").val()}`.trim()],
                    [`Document Type:`, `${dict[$(".dropdown-4").val()]}`.trim()],
                    [`Division By URL:`, `${dict[$(".dropdown-5").val()]}`.trim()],
                ];

                const filtersAreEmpty = appliedFilt.every((filter) => {
                    return filter[1] === "" || filter[1] === "undefined";
                });

                // Remove the second row with the filters
                if (lines.length > 2) {
                    lines.splice(1, 1);
                }
                let alteredLines = [];
                lines.forEach((line) => {
                    let newLine = "";
                    newLine = line.replace("open_in_new", "");
                    alteredLines.push(newLine);
                });

                if (filtersAreEmpty) return alteredLines.join("\n");
                else {
                    // Add filter information to the first row
                    const secondRowFilters = [
                    "Export of SDE Delta URLs",
                    `"(Applied Filters: ${appliedFilt
                        .reduce((acc, curr) => {
                        if (
                            curr[1] !== " undefined" &&
                            curr[1] !== " " &&
                            curr[1] !== "" &&
                            curr[1] !== "undefined"
                        ) {
                            acc = `${acc}, ${curr[0]} ${curr[1]}`;
                        }
                        return acc;
                        }, "")
                        .slice(2)})"`,
                    ];

                    var appliedFiltersInfo = secondRowFilters.join("\n");
                    return appliedFiltersInfo + "\n" + alteredLines.join("\n");
                }
                },
            },
            "spacer",
            {
                text: "Customize Columns",
                className: "customizeColumns",
                action: function () {
                modalContents("#delta_urls_table");
                },
            },
            ],
        },
        },
        serverSide: true,
        orderCellsTop: true,
        pagingType: "input",
        rowId: "url",
        stateLoadCallback: function (settings) {
        var state = JSON.parse(
            localStorage.getItem(
            "DataTables_delta_urls_" + window.location.pathname
            )
        );
        if (!state) {
            settings.oInit.pageLength = 1;
        }
        return state;
        },
        ajax: {
        url: `/api/delta-urls/?format=datatables&collection_id=${collection_id}`,
        data: function (d) {
            d.is_excluded = $("#filter-checkbox").is(":checked") ? false : null;
        },
        },
        initComplete: function (data) {
        const addDropdownSelect = [1, 4, 5];
        const dict = {
            1: "Images",
            2: "Data",
            3: "Documentation",
            4: "Software and Tools",
            5: "Missions and Instruments",
        };
        this.api()
            .columns()
            .every(function (index) {
            let column = this;
            if (addDropdownSelect.includes(index)) {
                $("thead tr td select.dropdown-" + index).on("change", function () {
                var val = $.fn.dataTable.util.escapeRegex($(this).val());
                column.search(val ? "^" + val + "$" : "", true, false).draw();
                });
            }
            });
        },

        columns: [
        getURLColumn(),
        getExcludedColumn(true_icon, false_icon),
        getScrapedTitleColumn(),
        getGeneratedTitleColumn(),
        getDocumentTypeColumn(),
        getDivisionColumn(),
        { data: "id", visible: false, searchable: false },
        { data: "generated_title_id", visible: false, searchable: false },
        { data: "match_pattern_type", visible: false, searchable: false },
        { data: "delta_urls_count", visible: false, searchable: false },
        { data: "excluded", visible: false, searchable: false },
        {
            data: null,
            render: function (data, type, row) {
            if (!row.document_type) return "Select";
            return dict[row.document_type];
            },
            visible: false,
        },
        {
            data: null,
            render: function (data, type, row) {
            const excludedDict = {
                true: "Yes",
                false: "No",
            };
            return excludedDict[row.excluded];
            },
            visible: false,
        },
        {
            data: null,
            render: function (data, type, row) {
            return row.generated_title;
            },
            visible: false,
        },
        // ...(is_multi_division === 'true' ? [getDivisionColumn()] : []),
        // getDivisionColumn(),
        ],
        createdRow: function (row, data, dataIndex) {
        if (data["excluded"]) {
            $(row).attr(
            "style",
            "background-color: rgba(255, 61, 87, 0.36) !important"
            );
        }
        },
        });
        },

    curatedUrls: function(collection_id) {
    return $('#curated_urls_table').DataTable({
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
                extend: "csv",
                exportOptions: {
                columns: [0, 11, 2, 12, 10],
                },
                customize: function (csv) {
                var lines = csv.split("\n");

                // Reorder the header columns
                var headers = lines[0].split(",");
                headers[4] = "New Title";
                var reorderedHeaders = [
                    headers[0],
                    headers[3],
                    headers[1],
                    headers[4],
                    headers[5],
                    headers[2],
                ];
                lines[0] = reorderedHeaders.join(",");

                const appliedFilt = [
                    [`URL:`, `${$("#curatedUrlFilter").val()}`.trim()],
                    [`Exclude:`, `${$(".dropdown-1").val()}`.trim()],
                    [
                    `Scraped Title:`,
                    `${$("#curatedScrapedTitleFilter").val()}`.trim(),
                    ],
                    [`New Title:`, `${$("#curatedNewTitleFilter").val()}`.trim()],
                    [`Document Type:`, `${dict[$(".dropdown-4").val()]}`.trim()],
                    [`Division By URL:`, `${dict[$(".dropdown-5").val()]}`.trim()],
                ];

                const filtersAreEmpty = appliedFilt.every((filter) => {
                    return filter[1] === "" || filter[1] === "undefined";
                });

                // Remove the second row with the filters
                if (lines.length > 2) {
                    lines.splice(1, 1);
                }
                let alteredLines = [];
                lines.forEach((line) => {
                    let newLine = "";
                    newLine = line.replace("open_in_new", "");
                    alteredLines.push(newLine);
                });

                if (filtersAreEmpty) return alteredLines.join("\n");
                else {
                    // Add filter information to the first row
                    const secondRowFilters = [
                    "Export of SDE Curated URLs",
                    `"(Applied Filters: ${appliedFilt
                        .reduce((acc, curr) => {
                        if (
                            curr[1] !== " undefined" &&
                            curr[1] !== " " &&
                            curr[1] !== "" &&
                            curr[1] !== "undefined"
                        ) {
                            acc = `${acc}, ${curr[0]} ${curr[1]}`;
                        }
                        return acc;
                        }, "")
                        .slice(2)})"`,
                    ];

                    var appliedFiltersInfo = secondRowFilters.join("\n");
                    return appliedFiltersInfo + "\n" + alteredLines.join("\n");
                }
                },
            },
            "spacer",
            {
                text: "Customize Columns",
                className: "customizeColumns",
                action: function () {
                modalContents("#curated_urls_table");
                },
            },
            ],
        },
        },
        serverSide: true,
        orderCellsTop: true,
        pagingType: "input",
        rowId: "url",
        stateLoadCallback: function (settings) {
        var state = JSON.parse(
            localStorage.getItem(
            "DataTables_curated_urls_" + window.location.pathname
            )
        );
        if (!state) {
            settings.oInit.pageLength = 1;
        }
        return state;
        },
        ajax: {
        url: `/api/curated-urls/?format=datatables&collection_id=${collection_id}`,
        data: function (d) {
            d.is_excluded = $("#filter-checkbox").is(":checked") ? false : null;
        },
        },
        initComplete: function (data) {
        const addDropdownSelect = [1, 4, 5];
        const dict = {
            1: "Images",
            2: "Data",
            3: "Documentation",
            4: "Software and Tools",
            5: "Missions and Instruments",
        };
        this.api()
            .columns()
            .every(function (index) {
            let column = this;
            if (addDropdownSelect.includes(index)) {
                $("thead tr td select.dropdown-" + index).on("change", function () {
                var val = $.fn.dataTable.util.escapeRegex($(this).val());
                column.search(val ? "^" + val + "$" : "", true, false).draw();
                });
            }
            });
        },

        columns: [
        getCuratedURLColumn(),
        getCuratedExcludedColumn(true_icon, false_icon),
        getCuratedScrapedTitleColumn(),
        getCuratedGeneratedTitleColumn(),
        getCuratedDocumentTypeColumn(),
        getCuratedDivisionColumn(),
        { data: "id", visible: false, searchable: false },
        { data: "generated_title_id", visible: false, searchable: false },
        { data: "match_pattern_type", visible: false, searchable: false },
        { data: "curated_urls_count", visible: false, searchable: false },
        { data: "excluded", visible: false, searchable: false },
        {
            data: null,
            render: function (data, type, row) {
            if (!row.document_type) return "Select";
            return dict[row.document_type];
            },
            visible: false,
        },
        {
            data: null,
            render: function (data, type, row) {
            const excludedDict = {
                true: "Yes",
                false: "No",
            };
            return excludedDict[row.excluded];
            },
            visible: false,
        },
        {
            data: null,
            render: function (data, type, row) {
            return row.generated_title;
            },
            visible: false,
        },
        // ...(is_multi_division === 'true' ? [getDivisionColumn()] : []),
        // getDivisionColumn(),
        ],
        createdRow: function (row, data, dataIndex) {
        if (data["excluded"]) {
            $(row).attr(
            "style",
            "background-color: rgba(255, 61, 87, 0.36) !important"
            );
        }
        },
    });
    },

    excludePatterns: function(collection_id) {
    return $('#exclude_patterns_table').DataTable({
        // scrollY: true,
        dom: "lBrtip",
        buttons: [
        {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
            $modal = $("#excludePatternModal").modal();
            },
        },
        {
            text: "Customize Columns",
            className: "customizeColumns",
            action: function () {
            modalContents("#exclude_patterns_table");
            },
        },
        ],
        lengthMenu: [
        [25, 50, 100, 500],
        ["Show 25", "Show 50", "Show 100", "Show 500"],
        ],
        orderCellsTop: true,
        pageLength: 100,
        ajax: `/api/exclude-patterns/?format=datatables&collection_id=${collection_id}`,
        initComplete: function (data) {
        var table = $("#exclude_patterns_table").DataTable();

        this.api()
            .columns()
            .every(function (index) {
            let column = this;
            if (column.data().length === 0) {
                $("#exclude-patterns-dropdown-1").prop("disabled", true);
            } else if (index === 1) {
                $("#exclude-patterns-dropdown-1").on("change", function () {
                if ($(this).val() === "") table.columns(6).search("").draw();
                else {
                    table
                    .column(6)
                    .search(matchPatternTypeMap[$(this).val()])
                    .draw();
                }
                });
            }
            });
        },
        columns: [
        { data: "match_pattern", class: "whiteText" },
        {
            data: "match_pattern_type_display",
            class: "text-center whiteText",
            sortable: true,
        },
        {
            data: "reason",
            class: "text-center whiteText",
            sortable: false,
            visible: false,
        },
        {
            data: "delta_urls_count",
            class: "text-center whiteText",
            sortable: true,
        },
        {
            data: null,
            sortable: false,
            class: "text-center",
            render: function (data, type, row) {
            return `<button class="btn btn-danger btn-sm delete-exclude-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
            },
        },
        { data: "id", visible: false, searchable: false },
        { data: "match_pattern_type", visible: false },
        ],
    });
    },

    includePatterns: function(collection_id) {
    return $('#include_patterns_table').DataTable({
        // scrollY: true,
        lengthMenu: [
            [25, 50, 100, 500],
            ["Show 25", "Show 50", "Show 100", "Show 500"],
        ],
        dom: "lBrtip",
        buttons: [
            {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
                $modal = $("#includePatternModal").modal();
            },
            },
            {
            text: "Customize Columns",
            className: "customizeColumns",
            action: function () {
                modalContents("#include_patterns_table");
            },
            },
        ],
        pageLength: 100,
        orderCellsTop: true,
        ajax: `/api/include-patterns/?format=datatables&collection_id=${collection_id}`,
        initComplete: function (data) {
            var table = $("#include_patterns_table").DataTable();
            this.api()
            .columns()
            .every(function (index) {
                let column = this;
                if (column.data().length === 0) {
                $("#include-patterns-dropdown-1").prop("disabled", true);
                } else {
                if (index === 1) {
                    $("#include-patterns-dropdown-1").on("change", function () {
                    if ($(this).val() === "") table.columns(5).search("").draw();
                    table
                        .column(5)
                        .search(matchPatternTypeMap[$(this).val()])
                        .draw();
                    });
                }
                }
            });
        },
        columns: [
            { data: "match_pattern", class: "whiteText" },
            {
            data: "match_pattern_type_display",
            class: "text-center whiteText",
            sortable: false,
            },
            {
            data: "delta_urls_count",
            class: "text-center whiteText",
            sortable: true,
            },
            {
            data: null,
            sortable: false,
            class: "text-center",
            render: function (data, type, row) {
                return `<button class="btn btn-danger btn-sm delete-include-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
            },
            },
            { data: "id", visible: false, searchable: false },
            { data: "match_pattern_type", visible: false },
        ],
    });
    },

    titlePatterns: function(collection_id) {
    return $('#title_patterns_table').DataTable({
        // scrollY: true,
        dom: "lBrtip",
        serverSide: true,
        paging: true,
        buttons: [
        {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
            $modal = $("#titlePatternModal").modal();
            },
        },
        {
            text: "Customize Columns",
            className: "customizeColumns",
            action: function () {
            modalContents("#title_patterns_table");
            },
        },
        ],
        lengthMenu: [
        [25, 50, 100, 500, -1],
        ["Show 25", "Show 50", "Show 100", "Show 500", "Show All"],
        ],
        pageLength: 50,
        orderCellsTop: true,
        ajax: `/api/title-patterns/?format=datatables&collection_id=${collection_id}`,
        initComplete: function (data) {
        var table = $("#title_patterns_table").DataTable();

        this.api()
            .columns()
            .every(function (index) {
            let column = this;
            if (column.data().length === 0) {
                $("#title-patterns-dropdown-1").prop("disabled", true);
            } else if (index === 1) {
                $("#title-patterns-dropdown-1").on("change", function () {
                if ($(this).val() === "") table.columns(6).search("").draw();
                else {
                    table
                    .column(6)
                    .search(matchPatternTypeMap[$(this).val()])
                    .draw();
                }
                });
            }
            });
        },
        columns: [
        { data: "match_pattern", class: "whiteText" },
        {
            data: "match_pattern_type_display",
            class: "text-center whiteText",
            sortable: false,
        },
        { data: "title_pattern", class: "whiteText" },
        {
            data: "delta_urls_count",
            class: "text-center whiteText",
            sortable: true,
        },
        {
            data: null,
            sortable: false,
            class: "text-center",
            render: function (data, type, row) {
            return `<button class="btn btn-danger btn-sm delete-title-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
            },
        },
        { data: "id", visible: false, searchable: false },
        { data: "match_pattern_type", visible: false },
        ],
    });
    },

    documentTypePatterns: function(collection_id) {
    return $('#document_type_patterns_table').DataTable({
        // scrollY: true,
        dom: "lBrtip",
        buttons: [
        {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
            $modal = $("#documentTypePatternModal").modal();
            },
        },
        {
            text: "Customize Columns",
            className: "customizeColumns",
            action: function () {
            modalContents("#document_type_patterns_table");
            },
        },
        ],
        lengthMenu: [
        [25, 50, 100, 500],
        ["Show 25", "Show 50", "Show 100", "Show 500"],
        ],
        orderCellsTop: true,
        pageLength: 100,
        ajax: `/api/document-type-patterns/?format=datatables&collection_id=${collection_id}`,
        initComplete: function (data) {
        this.api()
            .columns()
            .every(function (index) {
            var table = $("#document_type_patterns_table").DataTable();

            let addDropdownSelect = {
                1: {
                columnToSearch: 6,
                matchPattern: {
                    "Individual URL Pattern": 1,
                    "Multi-URL Pattern": 2,
                },
                },
                2: {
                columnToSearch: 7,
                matchPattern: {
                    Images: 1,
                    Data: 2,
                    Documentation: 3,
                    "Software and Tools": 4,
                    "Missions and Instruments": 5,
                },
                },
            };

            let column = this;
            if (column.data().length === 0) {
                $(`#document-type-patterns-dropdown-${index}`).prop(
                "disabled",
                true
                );
            } else if (index in addDropdownSelect) {
                $("#document-type-patterns-dropdown-" + index).on(
                "change",
                function () {
                    let col = addDropdownSelect[index].columnToSearch;
                    let searchInput =
                    addDropdownSelect[index].matchPattern[$(this).val()];
                    if ($(this).val() === "" || $(this).val() === undefined)
                    table.columns(col).search("").draw();
                    else {
                    table.columns(col).search(searchInput).draw();
                    }
                }
                );
            }
            });
        },

        columns: [
        { data: "match_pattern", class: "whiteText" },
        {
            data: "match_pattern_type_display",
            class: "text-center whiteText",
            sortable: false,
        },
        { data: "document_type_display", class: "whiteText" },
        {
            data: "delta_urls_count",
            class: "text-center whiteText",
            sortable: true,
        },
        {
            data: null,
            sortable: false,
            class: "text-center",
            render: function (data, type, row) {
            return `<button class="btn btn-danger btn-sm delete-document-type-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
            },
        },
        { data: "id", visible: false, searchable: false },
        { data: "match_pattern_type", visible: false },
        { data: "document_type", visible: false },
        ],
    });
    },

    divisionPatterns: function(collection_id) {
    return $('#division_patterns_table').DataTable({
        dom: "lBrtip",
        buttons: [
            {
            text: "Add Pattern",
            className: "addPattern",
            action: function () {
                $modal = $("#divisionPatternModal").modal();
            },
            },
            {
            text: "Customize Columns",
            className: "customizeColumns",
            action: function () {
                modalContents("#division_patterns_table");
            },
            },
        ],
        lengthMenu: [
            [25, 50, 100, 500],
            ["Show 25", "Show 50", "Show 100", "Show 500"],
        ],
        orderCellsTop: true,
        pageLength: 100,
        ajax: `/api/division-patterns/?format=datatables&collection_id=${collection_id}`,
        initComplete: function (data) {
            this.api()
            .columns()
            .every(function (index) {
                var table = $("#division_patterns_table").DataTable();

                let addDropdownSelect = {
                1: {
                    columnToSearch: 6,
                    matchPattern: {
                    "Individual URL Pattern": 1,
                    "Multi-URL Pattern": 2,
                    },
                },
                2: {
                    columnToSearch: 7,
                    matchPattern: {
                    "Astrophysics": 1,
                    "Biological and Physical Sciences": 2,
                    "Earth Science": 3,
                    "Heliophysics": 4,
                    "Planetary Science": 5,
                    },
                },
                };

                let column = this;
                if (column.data().length === 0) {
                $(`#division-patterns-dropdown-${index}`).prop("disabled", true);
                } else if (index in addDropdownSelect) {
                $("#division-patterns-dropdown-" + index).on("change", function () {
                    let col = addDropdownSelect[index].columnToSearch;
                    let searchInput =
                    addDropdownSelect[index].matchPattern[$(this).val()];
                    if ($(this).val() === "" || $(this).val() === undefined)
                    table.columns(col).search("").draw();
                    else {
                    table.columns(col).search(searchInput).draw();
                    }
                });
                }
            });
        },

        columns: [
            { data: "match_pattern", class: "whiteText" },
            {
            data: "match_pattern_type_display",
            class: "text-center whiteText",
            sortable: false,
            },
            { data: "division_display", class: "whiteText" },
            {
            data: "delta_urls_count",
            class: "text-center whiteText",
            sortable: true,
            },
            {
            data: null,
            sortable: false,
            class: "text-center",
            render: function (data, type, row) {
                return `<button class="btn btn-danger btn-sm delete-division-pattern-button" data-row-id="${row["id"]}"><i class="material-icons">delete</i></button >`;
            },
            },
            { data: "id", visible: false, searchable: false },
            { data: "match_pattern_type", visible: false },
            { data: "division", visible: false },
        ],
    });
    }
  };
