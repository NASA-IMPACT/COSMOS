////////////////// Division ////////////////////////////
let divisionChart = document.getElementById("divisionChart").getContext("2d");

const labels = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
    "November", "December"
];
const divisionData = {
    labels: labels,
    datasets: [{
        label: 'Total SDE Entries',
        data: [65, 59, 80, 81, 56, 55, 40, 43, 7, 50, 12, 52],
        fill: true,
        borderColor: '#65B1EF',
        tension: 0.1
    }]
};

const stackedLine = new Chart(divisionChart, {
    type: 'line',
    data: divisionData,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Total SDE Entries',
                position: 'top',
                align: 'start',
                color: '#A7BACD',
                font: {
                    family: 'sans-serif',
                    size: 14,
                    weight: '400',
                },
            },
            subtitle: {
                display: true,
                position: 'top',
                align: 'start',
                padding: 10,
                text: '3000',
                color: '#65B1EF',
                font: {
                    size: 24,
                    family: 'sans-serif',
                    weight: '700',
                },
            },
        },
        scales: {
            y: {
                stacked: true,
                grid: {
                    color: '#A7BACD'
                }
            }
        }
    }
});
/////////////////////////////////////////////
////// candidiate urls /////////////////////
let urlChart = document.getElementById("urlChart").getContext("2d");

const urlData = {
    labels: labels,
    datasets: [{
        label: 'Total Scraped URLs',
        data: [6512, 59, 800, 81, 56, 55, 40, 4300, 7, 50, 120, 520],
        fill: true,
        borderColor: '#65B1EF',
        tension: 0.1
    }]
};

const stackedLine2 = new Chart(urlChart, {
    type: 'line',
    data: urlData,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Total Scraped URLs',
                position: 'top',
                align: 'start',
                color: '#A7BACD',
                font: {
                    family: 'sans-serif',
                    size: 14,
                    weight: '400',
                },
            },
            subtitle: {
                display: true,
                position: 'top',
                align: 'start',
                padding: 10,
                text: '5280',
                color: '#65B1EF',
                font: {
                    size: 24,
                    family: 'sans-serif',
                    weight: '700',
                },
            },
        },
        scales: {
            y: {
                stacked: true,
                grid: {
                    color: '#A7BACD'
                }
            }
        }
    }
});
//////////////////////////////////////////////////////////////
/////////////// Workflow status ///////////////////////////////
let workflowChart = document.getElementById("workflowChart").getContext("2d");

const workflowData = {
    labels: ["Research in Progress", "Ready for Engineering", "Engineering in Progress", "Ready for Curation",
        "Curation in Progress",
        "Curated",
        "Quality Fixed",
        "Secret Deployment Started",
        "Secret Deployment Failed",
        "Ready for LRM Quality Check",
        "Ready for Quality Check",
        "Quality Check Failed",
        "Ready for Public Production",
        "Perfect and on Production",
        "Low Priority Problems on Production",
        "High Priority Problems on Production, only for old sources",
        "Code Merge Pending"
    ],
    datasets: [{
        label: 'Workflow Status Counts',
        data: [651, 59, 800, 81, 56, 550, 40, 430, 7, 50, 120, 520, 13, 14, 15, 16, 17],
        backgroundColor: [
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
        ],
        borderColor: [
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
            '#65B1EF',
        ],
        borderWidth: 1

    }]
};

const barChart = new Chart(workflowChart, {
    type: 'bar',
    data: workflowData,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Workflow Status Counts',
                position: 'top',
                padding: 20,
                align: 'start',
                color: '#A7BACD',
                font: {
                    family: 'sans-serif',
                    size: 14,
                    weight: '400',
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
            x: {  // not 'xAxes: [{' anymore (not an array anymore)
                ticks: {
                    color: "white",  // not 'fontColor:' anymore
                    //fontSize: 14,

                    beginAtZero: true
                }
            }

        }
    }
});
///////////////////////////////////////////////////////////////
///////////////// Curator /////////////////////////

