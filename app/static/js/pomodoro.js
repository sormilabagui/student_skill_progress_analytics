let time = 25 * 60;
let timer;
let isBreak = false;
let paused = false;

let startTime;
let pausedTime = 0;

const timerDisplay = document.getElementById("timer");

let todaySessions = 0;
let todayMinutes = 0;

const todaySessionsDisplay =
document.getElementById("todaySessions");

const todayHoursDisplay =
document.getElementById("todayHours");

const motivationText =
document.getElementById("motivationText");

function updateDisplay() {

let minutes = Math.floor(time / 60);
let seconds = time % 60;

timerDisplay.innerText =
`${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;

}


document.getElementById("start").onclick = function() {

if(timer) return;

startTime = new Date();

timer = setInterval(() => {

if(!paused){

time--;

updateDisplay();

if(time <= 0){

clearInterval(timer);
timer = null;

alarm();

saveProgress();

if(!isBreak){

isBreak = true;
time = 5 * 60;

alert("Break Time");

}else{

isBreak = false;
time = 25 * 60;

alert("Focus Time");

}

updateDisplay();

}

}

},1000);

};


document.getElementById("pause").onclick = function(){

paused = !paused;

this.innerText = paused ? "Resume" : "Pause";

};


document.getElementById("stop").onclick = function(){

clearInterval(timer);

timer = null;

saveProgress();

time = 25 * 60;
updateDisplay();

};


function alarm(){

let audio = new Audio(
"https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg"
);

audio.play();

}


function saveProgress(){

if(!startTime) return;

let endTime = new Date();

let diff = (endTime - startTime) / 1000;

let minutes = diff / 60;

if(minutes < 0.5) return; // ignore very small sessions

todaySessions++;

todayMinutes += minutes;

todaySessionsDisplay.innerText =
"Today's Sessions: " + todaySessions;

todayHoursDisplay.innerText =
"Today's Focus: " +
(todayMinutes/60).toFixed(2) + " hrs";

updateMotivation();

let skill = document.getElementById("skillSelect").value;

fetch("/save-pomodoro", {

method:"POST",

headers:{
"Content-Type":"application/json"
},

body: JSON.stringify({

skill_id: skill,
minutes: minutes

})

});

startTime = null;

}

window.addEventListener("beforeunload", function (e) {

if(timer){

saveProgress();

e.preventDefault();
e.returnValue = '';

}

});

updateDisplay();

const focusBtn = document.getElementById("focusModeBtn");
const exitFocusBtn = document.getElementById("exitFocusBtn");

focusBtn.onclick = function(){

document.body.classList.add("focus-mode");

focusBtn.style.display = "none";
exitFocusBtn.style.display = "inline-block";

}

exitFocusBtn.onclick = function(){

document.body.classList.remove("focus-mode");

focusBtn.style.display = "inline-block";
exitFocusBtn.style.display = "none";

}

const motivationMessages = [

"Stay focused. You're building your future.",
"Small progress daily leads to big success.",
"One session closer to your dream job.",
"Consistency beats motivation.",
"Your future self will thank you.",
"Discipline creates success."

];

function updateMotivation(){

let random =
Math.floor(Math.random() *
motivationMessages.length);

motivationText.innerText =
motivationMessages[random];

}