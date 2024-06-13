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
                },
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Number of Entries',
                    color:'white'
                } 
            },
            x: { 
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Months',
                    color:'white'
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
                },
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Number of URLs',
                    color:'white'
                } 
            },
            x: {
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Months',
                    color:'white'
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
        label: 'Total',
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
                text: 'Workflow Status Totals',
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
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Totals',
                    color:'white'
                } 
            },
            x: { 
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Statuses',
                    color:'white'
                } 
            }

        }
    }
});
///////////////////////////////////////////////////////////////
///////////////// Curator /////////////////////////
let sdeChart = document.getElementById("sdeChart").getContext("2d");

const stackedLine3 = new Chart(sdeChart, {
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
                },
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Number of Entries',
                    color:'white'
                } 
            },
            x: {
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Months',
                    color:'white'
                } 
            }
        }
    }
});


let divisionChart2 = document.getElementById("divisionChart2").getContext("2d");

const division2Data = {
    labels: ["Astrophysics", "Biological and Physical Sciences", "Earth Science",
    "Heliophysics", "Planetary Science", "General"
    ],
    datasets: [{
        label: 'Total',
        data: [25, 90, 120, 12, 56, 132],
        backgroundColor: [
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
        ],
        borderWidth: 1

    }]
};

const barChart2 = new Chart(divisionChart2, {
    type: 'bar',
    data: division2Data,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Entries by Division',
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
            subtitle: {
                display: true,
                position: 'top',
                align: 'start',
                padding: 10,
                text: '4561',
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
                beginAtZero: true,
                ticks: {
                    color: "white", 
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Totals',
                    color:'white'
                } 
            },
            x: {
                ticks: {
                    color: "white",
                    beginAtZero: true
                },
                title:{
                    display:true,
                    text: 'Divisions',
                    color:'white'
                } 
            }

        }
    }
});

let pieChart = document.getElementById("pieChart").getContext("2d");

const pieChartData = {
    labels: [
      'Not Started',
      'In Progress',
      'In Production'
    ],
    datasets: [{
      label: 'Workflow Status Completion',
      data: [300, 50, 100],
      backgroundColor: [
        '#F4C534',
        '#09B66D',
        '#65B1EF'
      ],
      hoverOffset: 4
    }]
  };

  const doughnutChart = new Chart(pieChart, {
    type: 'doughnut',
    data: pieChartData,
    options: {

        plugins: {
            legend: {
                display: true,
                position:'bottom',
                labels: {
                    color:'white'
                }
            },
            title: {
                display: true,
                text: 'Workflow Status Completion',
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
    }

  });

  let timeSpentChart = document.getElementById("timeSpentChart").getContext("2d");


const timeLabels = ["12 AM", "8 AM", "4 PM", "11 PM"];

const notStartedData = {
    labels: timeLabels,
    datasets: [{
        label: 'Not Started',
        data: [250, 390, 400, 81],
        fill: true,
        borderColor: '#65B1EF',
        tension: 0.1
    },
    {
        label: 'In Production',
        data: [150, 590, 20, 810],
        fill: true,
        borderColor: 'red',
        tension: 0.1
    },
    {
        label: 'In Progress',
        data: [20, 293, 630, 124],
        fill: true,
        borderColor: 'green',
        tension: 0.1
    }]
};


const stackedLine4 = new Chart(timeSpentChart, {
    type: 'line',
    data: notStartedData,
    options: {

        plugins: {
            legend: {
                display: true,
                position:'bottom',
                labels: {
                    color:'white'
                }
            },
            title: {
                display: true,
                text: 'Total time spent',
                position: 'top',
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
                stacked: true,
                grid: {
                    color: '#A7BACD'
                },
                title:{
                    display:true,
                    text: 'Number of Entries',
                    color:'white'
                } 
            },
            x: {
                title:{
                    display:true,
                    text: 'Time',
                    color:'white'
                } 
            }
        }
    }
});

