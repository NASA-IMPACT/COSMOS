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
            // ... curated urls table config
        });
        },

        excludePatterns: function(collection_id) {
        return $('#exclude_patterns_table').DataTable({
            // ... exclude patterns table config
        });
        },

        includePatterns: function(collection_id) {
        return $('#include_patterns_table').DataTable({
            // ... include patterns table config
        });
        },

        titlePatterns: function(collection_id) {
        return $('#title_patterns_table').DataTable({
            // ... title patterns table config
        });
        },

        documentTypePatterns: function(collection_id) {
        return $('#document_type_patterns_table').DataTable({
            // ... document type patterns table config
        });
        },

        divisionPatterns: function(collection_id) {
        return $('#division_patterns_table').DataTable({
            // ... division patterns table config
        });
    }
  };
