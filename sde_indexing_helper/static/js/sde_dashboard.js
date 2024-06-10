let ctx = document.getElementById("chart").getContext("2d");

// let chart = new Chart(ctx, {
//   type: "bar",
//   data: {
//      labels: ["2020/Q1", "2020/Q2", "2020/Q3", "2020/Q4"],
//      datasets: [
//         {
//           label: "Gross volume ($)",
//           backgroundColor: "#79AEC8",
//           borderColor: "#417690",
//           data: [26900, 28700, 27300, 29200]
//         }
//      ]
//   },
//   options: {
//      title: {
//         text: "Gross Volume in 2020",
//         display: true
//      }
//   }
// });


const labels = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
"November", "December"
];
const data = {
  labels: labels,
  datasets: [{
    label: 'Total SDE Entries',
    data: [65, 59, 80, 81, 56, 55, 40, 43,7,50,12,52],
    fill: false,
    borderColor: 'rgb(75, 192, 192)',
    tension: 0.1
  }]
};

const stackedLine = new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
        scales: {
            y: {
                stacked: true
            }
        }
    }
});


