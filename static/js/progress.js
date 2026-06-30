// =========================================
// SMART PROGRESS TRACKER
// =========================================

const timers = {};

// =========================================
// FORMAT TIME
// =========================================

function formatTime(seconds){

    const hrs = Math.floor(seconds / 3600);

    const mins = Math.floor((seconds % 3600) / 60);

    const secs = seconds % 60;

    return String(hrs).padStart(2,"0")
        + ":"
        + String(mins).padStart(2,"0")
        + ":"
        + String(secs).padStart(2,"0");

}

// =========================================
// START TIMER
// =========================================

document.querySelectorAll(".start-btn").forEach(button=>{

    button.addEventListener("click",()=>{

        const taskId = button.dataset.id;

        if(timers[taskId]) return;

        let timerElement =
            document.getElementById(
                "timer-"+taskId
            );

        let seconds = 0;

        timers[taskId] = setInterval(()=>{

            seconds++;

            timerElement.innerHTML =
                formatTime(seconds);

        },1000);

    });

});

// =========================================
// PAUSE TIMER
// =========================================

document.querySelectorAll(".pause-btn").forEach(button=>{

    button.addEventListener("click",()=>{

        const taskId = button.dataset.id;

        clearInterval(timers[taskId]);

        delete timers[taskId];

    });

});

// =========================================
// FINISH TASK
// =========================================

document.querySelectorAll(".finish-btn").forEach(button=>{

    button.addEventListener("click",()=>{

        const taskId = button.dataset.id;

        clearInterval(timers[taskId]);

        delete timers[taskId];

        alert("Task Completed!");

    });

});