document.addEventListener('DOMContentLoaded', function () {

    const calendarEl = document.getElementById('calendar');

    const eventList = document.getElementById('event-list');

    const calendar = new FullCalendar.Calendar(calendarEl, {

        initialView: 'dayGridMonth',

        height: 700,

        selectable: true,

        events: "/calendar-events",

        dateClick:function(info){

            const events = calendar.getEvents().filter(

                e => e.startStr === info.dateStr

            );

            showEvents(events);

        }

    });

    calendar.render();

    function showEvents(events){

        eventList.innerHTML="";

        if(events.length===0){

            eventList.innerHTML="<p>No Events</p>";

            return;

        }

        events.forEach(event=>{

            let cls="low";

            if(event.extendedProps.priority==="HIGH")

                cls="high";

            else if(event.extendedProps.priority==="MEDIUM")

                cls="medium";

            eventList.innerHTML+=`

            <div class="event-card ${cls}">

                <h3>${event.title}</h3>

                <p>Priority : ${event.extendedProps.priority}</p>

            </div>

            `;

        });

    }

});