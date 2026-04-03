document.addEventListener("DOMContentLoaded", function () {

    // Skill Progress Chart
    const skillCanvas = document.getElementById("skillChart");

    const labels = JSON.parse(skillCanvas.dataset.labels);
    const progress = JSON.parse(skillCanvas.dataset.progress);

    new Chart(skillCanvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Skill Progress (%)",
                data: progress,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });



    // Category Pie Chart
    const categoryCanvas = document.getElementById("categoryChart");

    const categoryLabels = JSON.parse(categoryCanvas.dataset.labels);
    const categoryValues = JSON.parse(categoryCanvas.dataset.values);

    new Chart(categoryCanvas, {
        type: "pie",
        data: {
            labels: categoryLabels,
            datasets: [{
                data: categoryValues
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });



    // Weekly Target Chart
    const weeklyCanvas = document.getElementById("weeklyChart");

    const weeklyLabels = JSON.parse(weeklyCanvas.dataset.labels);
    const weeklyData = JSON.parse(weeklyCanvas.dataset.data);

    new Chart(weeklyCanvas, {
        type: "bar",
        data: {
            labels: weeklyLabels,
            datasets: [{
                label: "Target Hours",
                data: weeklyData
            }]
        },
        options: {
            responsive: true
        }
    });

});

let timer;
let timeLeft = 25 * 60;
let startTime;
let isPaused = false;

function startTimer() {

    if (!isPaused) {
        startTime = new Date();
    }

    clearInterval(timer);

    timer = setInterval(() => {

        timeLeft--;

        let minutes = Math.floor(timeLeft / 60);
        let seconds = timeLeft % 60;

        document.getElementById("timer").innerText =
        `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

        if (timeLeft <= 0) {

            clearInterval(timer);
            saveProgress();

            alert("Pomodoro Completed!");

            resetTimer();
        }

    }, 1000);

    isPaused = false;
    document.getElementById("pauseBtn").innerText = "Pause";
}

function pauseTimer() {

    if (!isPaused) {

        clearInterval(timer);
        isPaused = true;

        document.getElementById("pauseBtn").innerText = "Resume";

    } else {

        startTimer();
    }

}

function stopTimer() {

    clearInterval(timer);

    saveProgress();

    resetTimer();

}

function resetTimer() {

    timeLeft = 25 * 60;
    document.getElementById("timer").innerText = "25:00";
    document.getElementById("pauseBtn").innerText = "Pause";
    isPaused = false;
}

function saveProgress() {

    const skillId = document.getElementById("skillSelect").value;

    const endTime = new Date();

    const seconds = Math.floor((endTime - startTime) / 1000);

    const hours = seconds / 3600;

    if (hours <= 0) return;

    fetch("/timer-progress", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            skill_id: skillId,
            hours: hours
        })
    });

}