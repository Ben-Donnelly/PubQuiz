$(".about-bar").click(function() {
  $expandable = $(this);
  $content = $expandable.next();
  $content.slideToggle(500, function() {
    $expandable.text(function() {
      return $content.is(":visible") ? "Close" : "About";
    });
  });
});

$("#regForm :input").prop("disabled", true);
$("#regFormSubBut").prop("disabled", true);

var ctx = document.getElementById("canvas");

Chart.pluginService.register({
    afterDraw: function(chart) {
        if (typeof chart.config.options.lineAt != 'undefined') {
        	var lineAt = chart.config.options.lineAt;
            var ctxPlugin = chart.chart.ctx;
            var xAxe = chart.scales[chart.config.options.scales.xAxes[0].id];
            var yAxe = chart.scales[chart.config.options.scales.yAxes[0].id];

            if(yAxe.min != 0) return;

            ctxPlugin.strokeStyle = "white";
        	ctxPlugin.beginPath();
            lineAt = (lineAt - yAxe.min) * (100 / yAxe.max);
            lineAt = (100 - lineAt) / 100 * (yAxe.height) + yAxe.top;
            ctxPlugin.moveTo(xAxe.left, lineAt);
            ctxPlugin.lineTo(xAxe.right, lineAt);
            ctxPlugin.stroke();
        }
    }
});

var steps = 20;
function drawHorizontalChart()
{


    new Chart(document.getElementById("bar-chart-h"), {
        type: 'horizontalBar',
        data: {
          labels: cust_labels,
          datasets: [
            {
              backgroundColor: cust_colours,
              data: cust_data
            }
          ]
        },
        options: {
        indexAxis: 'y',
          legend: { display: false },
          title: {
            display: true,
            text: ''
          },
          scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true
                }
            }]
        },

        animation: {
                duration: 2000,
                easing: 'easeOutBounce',
            },

          annotation: {
          annotations: [{
            type: 'line',
            mode: 'horizontal',
            scaleID: 'y-axis-0',
            value: 100,
            borderColor: 'rgb(255, 255, 255)',
            borderWidth: 10,
            label: {
              enabled: true,
              content: 'Test label'
            }
                  }]
        },

          responsive: true,
          maintainAspectRatio: true,
          scaleOverride: true,
          scaleSteps: steps,
          scaleStepWidth: Math.ceil(max / steps),
          scaleStartValue: 0,
          scaleShowVerticalLines: true,
          scaleShowGridLines : true,
          barShowStroke : true,
          scaleShowLabels: true
        }
    });

};

function drawAvergaesChart()
{

new Chart(document.getElementById("bar-chart"), {
    type: 'bar',
    data: {
      labels: b_avg_with_names,
      datasets: [
        {
          backgroundColor: cust_colours,
          data: b_avg_scores
        }
      ]
    },
    options: {
      legend: { display: false },
      title: {
        display: true,
        text: ''
      },
      scales: {
        yAxes: [{
            ticks: {
                beginAtZero: true
            }
        }]
    },

    animation: {
            duration: 2000,
            easing: 'easeOutBounce',
        },
      // TODO: average of averages line
      lineAt: b_avg_of_avg,
//      annotation: {
//      annotations: [{
//        type: 'line',
//        mode: 'horizontal',
//        scaleID: 'y-axis-0',
//        value: b_avg_of_avg,
//        borderColor: 'rgb(255, 255, 255)',
//        borderWidth: 10,
//        label: {
//          enabled: true,
//          content: 'Test label'
//        }
//              }]
//    },

      responsive: true,
      maintainAspectRatio: true,
      scaleOverride: true,
      scaleSteps: steps,
      scaleStepWidth: Math.ceil(max / steps),
      scaleStartValue: 0,
      scaleShowVerticalLines: true,
      scaleShowGridLines : true,
      barShowStroke : true,
      scaleShowLabels: true
    }
});

};


function drawLineChart()
{
    console.log(average_of_averages);
    new Chart(document.getElementById("line-chart"), {
      type: 'line',
      data: {
        labels: line_graph_dict['x_axis'],
        datasets: [

    {
            data: line_graph_dict['score_dict']['Ben'],
            label: cust_labels[0],
            backgroundColor: cust_colours[0],
            pointRadius: 4,
            borderColor: cust_colours[0],
            fill: false
          },
            {
            data: line_graph_dict['score_dict']['Craig'],
            label: cust_labels[1],
            backgroundColor: cust_colours[1],
            pointRadius: 4,
            borderColor: cust_colours[1],
            fill: false
          }, {
            data: line_graph_dict['score_dict']['Hazelf8'],
            label: cust_labels[2],
            backgroundColor: cust_colours[2],
            pointRadius: 4,
            borderColor: cust_colours[2],
            fill: false
          }
        ]
      },
      options: {
       legend: {
        display: false,
      },

      scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true
                }
            }],

            xAxes: [{
                scaleLabel:
                {
                    display: true,
                    labelString: 'Week No.'
                }
            }]
        },
          tooltips: {
        callbacks: {
           title: function(tooltipItem, data) {
            return 'Week: ' + this._data.labels[tooltipItem[0].index];
        }
        }
      },
        title: {
          display: false,
          text: ''
        },

        responsive: true,
        maintainAspectRatio: true
      }

    });
}

function drawPieChart()
{
    new Chart(document.getElementById("pie-chart"), {
        type: 'pie',
        data: {
          labels: cust_labels,
          datasets: [{
            label: "",
            backgroundColor: cust_colours,
            data: cust_data
          }]
        },
        options: {
          legend:{
          display:false
        }
        }
    });
}

function drawUserLineChart(curr_user, score_stats)
{

new Chart(document.getElementById("line-chart-user"), {
      type: 'line',
      data: {
        labels: num_of_weeks,
        datasets: [

    {
            data: scores_l,
            label: cust_labels,
            backgroundColor: colour,
            pointRadius: 6,
            borderColor: colour,
            fill: false
          },

        ]
      },
      options: {
       legend: {
        display: false,
      },

      scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true
                }
            }],

            xAxes: [{
                scaleLabel:
                {
                    display: true,
                    labelString: 'Week No.'
                }
            }]
        },
          tooltips: {
        callbacks: {
           title: function(tooltipItem, data) {
            return 'Week: ' + this._data.labels[tooltipItem[0].index];
        }
        }
      },
        title: {
          display: false,
          text: ''
        },

        responsive: true,
        maintainAspectRatio: true
      }

    });





































//console.log(scores_l);
//    new Chart(document.getElementById("line-chart-user"), {
//      type: 'line',
//      data: {
////        labels: cust_labels,
//        datasets: [
//
//    {
//            data: scores_l,
//            label: cust_labels,
//            backgroundColor: colour,
//            pointRadius: 4,
//            borderColor: colour,
//            fill: false
//          }
//        ]
//      },
//      options: {
//       legend: {
//        display: false,
//      },
//
//      scales: {
//            yAxes: [{
//                ticks: {
//                    beginAtZero: true
//                }
//            }],
//
//            xAxes: [{
//                scaleLabel:
//                {
//                    display: true,
//                    labelString: 'Week No.'
//                }
//            }]
//        },
//          tooltips: {
//        callbacks: {
//           title: function(tooltipItem, data) {
//            return 'Week: ' + this._data.labels[tooltipItem[0].index];
//        }
//        }
//      },
//        title: {
//          display: false,
//          text: ''
//        },
//
//        responsive: true,
//        maintainAspectRatio: true
//      }
//
//    });
}
