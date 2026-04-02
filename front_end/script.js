 import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Declare the chart dimensions and margins.
const width = 575;
const height = 300;
const marginTop = 5;
const marginRight = 20;
const marginBottom = 30;
const marginLeft = 40;

let altData;
let tempData;
let gpsData;

//----------------------Altitide-------------------------
// set up x and y scales
const altX = d3.scaleLinear()
    //3 minutes
    .domain([0,50])
    .range([marginLeft, width - marginRight]);

const altY = d3.scaleLinear()
    .domain([2000, 3000])
    .range([height - marginBottom, marginTop]);

// 2. Fixed selector (#altcontainer) and variable names (altWidth)
const altSvg = d3.select("#altcontainer") 
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// 3. Add X-axis
const altXAxis = altSvg.append("g")
    .attr("class","x-axis")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(altX));

// 4. Add Y-axis (changed to axisLeft)
const altYAxis = altSvg.append("g")
    .attr("class","y-axis")
    .attr("transform", `translate(${marginLeft}, 0)`)
    .call(d3.axisLeft(altY));

// 5. Create altitude path
const altPath = altSvg.append("path")
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", 1);

// 6. Initiate line
const altLine = d3.line()
    .x(d => altX(d.time))
    .y(d => altY(d.val));



    //create tooltip
const altTooltip = d3.select("body")
    .append("div")
    .attr("class","tooltip")

//create circle
const altCircle = altSvg.append("circle")
    .attr("r",0)
    .attr("fill","black")
    .style("stroke","white")
    .attr("opacity",.70)
    .style("pointer-events","none");

//listening rectangle
  const altListeningRect = altSvg.append("rect")
    .attr("width", width)
    .attr("height", height);

  // create the mouse move function

altListeningRect.on("mousemove", function (event) {
    if (!altData || altData.length === 0) return;

    const [xCoord] = d3.pointer(event);
    const bisectDate = d3.bisector(d => d.time).left;
    const x0 = altX.invert(xCoord);
    
    // Find the closest data point
    const i = bisectDate(altData, x0, 1);
    const d0 = altData[i - 1];
    const d1 = altData[i];
    
    // Safety check for edges of the array
    if (!d1) return; 
    const d = x0 - d0.time > d1.time - x0 ? d1 : d0;

    const xPos = altX(d.time);
    const yPos = altY(d.val);

    // Update the circle position
    altCircle
        .attr("cx", xPos)
        .attr("cy", yPos)
        .attr("r", 5);

    // Update tooltip content and position
    altTooltip
        .style("display", "block")
        // Use event.pageX/Y for absolute positioning relative to the screen
        .style("left", `${event.pageX + 15}px`)
        .style("top", `${event.pageY - 15}px`)
        .html(`
            <strong>Time:</strong> ${d.time.toFixed(2)}s<br>
            <strong>Altitude:</strong> ${d.val.toFixed(2)}m
        `);
});

altListeningRect.on("mouseleave", function () {
    altCircle.attr("r", 0);
    altTooltip.style("display", "none");
});
//--------------------Temperature---------------------------   
// set up x and y scales
const tempX = d3.scaleLinear()
    .domain([0, 1000])
    .range([marginLeft, width - marginRight]);

const tempY = d3.scaleLinear()
    .domain([0, 100])
    .range([height - marginBottom, marginTop]);

// 2. Fixed selector (#altcontainer) and variable names (altWidth)
const tempSvg = d3.select("#tempcontainer") 
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// 3. Add X-axis
const tempXAxis = tempSvg.append("g")
    .attr("class","x-axis")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(tempX));

// 4. Add Y-axis (changed to axisLeft)
const tempYAxis = tempSvg.append("g")
    .attr("class","y-axis")
    .attr("transform", `translate(${marginLeft}, 0)`)
    .call(d3.axisLeft(tempY));

// 5. Create temperature path
const tempPath = tempSvg.append("path")
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", 1);

// 6. Initiate line
const tempLine = d3.line()
    .x(d => tempX(d.time))
    .y(d => tempY(d.val));

    //create tooltip
const tempTooltip = d3.select("body")
    .append("div")
    .attr("class","tooltip")

//create circle
const tempCircle = tempSvg.append("circle")
    .attr("r",0)
    .attr("fill","black")
    .style("stroke","white")
    .attr("opacity",.70)
    .style("pointer-events","none");

//listening rectangle
  const tempListeningRect = tempSvg.append("rect")
    .attr("width", width)
    .attr("height", height);

  // create the mouse move function

tempListeningRect.on("mousemove", function (event) {
    if (!tempData || tempData.length === 0) return;

    const [xCoord] = d3.pointer(event);
    const bisectDate = d3.bisector(d => d.time).left;
    const x0 = tempX.invert(xCoord);
    
    // Find the closest data point
    const i = bisectDate(tempData, x0, 1);
    const d0 = tempData[i - 1];
    const d1 = tempData[i];
    
    // Safety check for edges of the array
    if (!d1) return; 
    const d = x0 - d0.time > d1.time - x0 ? d1 : d0;

    const xPos = tempX(d.time);
    const yPos = tempY(d.val);

    // Update the circle position
    tempCircle
        .attr("cx", xPos)
        .attr("cy", yPos)
        .attr("r", 5);

    // Update tooltip content and position
    tempTooltip
        .style("display", "block")
        // Use event.pageX/Y for absolute positioning relative to the screen
        .style("left", `${event.pageX + 15}px`)
        .style("top", `${event.pageY - 15}px`)
        .html(`
            <strong>Time:</strong> ${d.time.toFixed(2)}s<br>
            <strong>Temperature:</strong> ${d.val.toFixed(2)}m
        `);
});

tempListeningRect.on("mouseleave", function () {
    tempCircle.attr("r", 0);
    tempTooltip.style("display", "none");
});
//----------------------GPS--------------------------

// set up x and y scales
const gpsX = d3.scaleLinear()
    .domain([102,103])
    .range([marginLeft, width - marginRight]);

const gpsY = d3.scaleLinear()
    .domain([31, 32])
    .range([height - marginBottom, marginTop]);

// 2. Fixed selector (#altcontainer) and variable names (altWidth)
const gpsSvg = d3.select("#gpscontainer") 
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// 3. Add X-axis
const gpsXAxis = gpsSvg.append("g")
    .attr("class","x-axis")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(gpsX));

// 4. Add Y-axis (changed to axisLeft)
const gpsYAxis = gpsSvg.append("g")
    .attr("class","y-axis")
    .attr("transform", `translate(${marginLeft}, 0)`)
    .call(d3.axisLeft(gpsY));

// 5. Create gps path
const gpsPath = gpsSvg.append("path")
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", 1);

// 6. Initiate line
const gpsLine = d3.line()
    .x(d => gpsX(d.gX))
    .y(d => gpsY(d.gY));


    //create tooltip
const gpsTooltip = d3.select("body")
    .append("div")
    .attr("class","tooltip")

//create circle
const gpsCircle = gpsSvg.append("circle")
    .attr("r",0)
    .attr("fill","black")
    .style("stroke","white")
    .attr("opacity",.70)
    .style("pointer-events","none");

//listening rectangle
  const gpsListeningRect = gpsSvg.append("rect")
    .attr("width", width)
    .attr("height", height);

  // create the mouse move function

gpsListeningRect.on("mousemove", function (event) {
    if (!gpsData || gpsData.length === 0) return;

    const [xCoord] = d3.pointer(event);
    const bisectDate = d3.bisector(d => d.gX).left;
    const x0 = gpsX.invert(xCoord);
    
    // Find the closest data point
    const i = bisectDate(gpsData, x0, 1);
    const d0 = gpsData[i - 1];
    const d1 = gpsData[i];
    
    // Safety check for edges of the array
    if (!d1) return; 
    const d = x0 - d0.gX > d1.gX - x0 ? d1 : d0;

    const xPos = gpsX(d.gX);
    const yPos = gpsY(d.gY);

    // Update the circle position
    gpsCircle
        .attr("cx", xPos)
        .attr("cy", yPos)
        .attr("r", 5);

    // Update tooltip content and position
    gpsTooltip
        .style("display", "block")
        // Use event.pageX/Y for absolute positioning relative to the screen
        .style("left", `${event.pageX + 15}px`)
        .style("top", `${event.pageY - 15}px`)
        .html(`
            <strong>X-Pos:</strong> ${d.gX.toFixed(2)}s<br>
            <strong>Y-Pos:</strong> ${d.gY.toFixed(2)}m
        `);
});

gpsListeningRect.on("mouseleave", function () {
    gpsCircle.attr("r", 0);
    gpsTooltip.style("display", "none");
});

const startbtn = document.getElementById("startbtn");

let record = false;

function toggleRecording() {
    if(!record){
        startbtn.innerHTML = "Stop Recording";
        record=true;
        startbtn.classList.add("on");
    }
    else{
        startbtn.innerHTML = "Start Recording"
        record = false;
        startbtn.classList.remove("on");
    }
} 
startbtn.addEventListener("click", toggleRecording);



async function postTelemetryData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/post_data", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // We don't need to send a body because the backend 
            // generates the data from the Sensor_reader class
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Data saved to MongoDB with ID:", result.id);
        
    } catch (error) {
        console.error("Failed to post data:", error);
    }
}

async function fetchData() {
    if (!record) return;

  try {
    // Await the fetch call and get the Response object
    const response = await fetch("http://127.0.0.1:8000/read_data");

    // Check if the request was successful
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Await the response.json() call to parse the body as JSON
    const data = await response.json();

    //transform data
    altData = data.altitude.timestamps.map((t, i) => ({
        time: t,
        val: data.altitude.values[i]
    }));
    if (altData.length > 0) {
        altX.domain([0, d3.max(altData, d => d.time) + 10]);
        altY.domain([0, d3.max(altData, d => d.val) + 10]);
        
        altXAxis.call(d3.axisBottom(altX));
        altYAxis.call(d3.axisLeft(altY));
        altPath.datum(altData).attr("d", altLine);
    }

    tempData = data.temperature.timestamps.map((t, i) => ({
        time: t,
        val: data.temperature.values[i]
    }));
    if (tempData.length > 0) {
        tempX.domain([0, d3.max(tempData, d => d.time) + 10]);
        tempY.domain([0, d3.max(tempData, d => d.val) + 10]);

        tempXAxis.call(d3.axisBottom(tempX));
        tempYAxis.call(d3.axisLeft(tempY));
        tempPath.datum(tempData).attr("d", tempLine);
    }

    gpsData = data.gps.x.map((a, b) => ({
        gX: a,
        gY: data.gps.y[b]
    }));
    if (gpsData.length > 0) {
        const xExtent = d3.extent(gpsData, d => d.gX);
        const yExtent = d3.extent(gpsData, d => d.gY);

        gpsX.domain([xExtent[0] - 0.5, xExtent[1] + 0.5]);
        gpsY.domain([yExtent[0] - 0.5, yExtent[1] + 0.5]);

        gpsXAxis.call(d3.axisBottom(gpsX));
        gpsYAxis.call(d3.axisLeft(gpsY));
        gpsPath.datum(gpsData).attr("d", gpsLine);
    }

    // update paths
    altPath.datum(altData).attr("d", altLine);

    tempPath.datum(tempData).attr("d", tempLine);
    
    gpsPath.datum(gpsData).attr("d", gpsLine);
    //console.log(altData)
    
  } catch (error) {
    // Handle any errors that occurred during the fetch operation
    console.error("Could not fetch data:", error);
  }

}

/*async function resetSensorData() {
    try {
        const response = await fetch('http://127.0.0.1:8000/reset', {
            method: 'POST', // Specify the method
            headers: {
                'Content-Type': 'application/json'
            },
            // If your reset needed data, you'd put it in 'body', 
            // but for a simple reset, we leave it out.
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Success:', data.message);
            alert('Sensor data has been cleared!');
        } else {
            console.error('Server error:', response.status);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}*/

const resetBtn = document.getElementById("resetbtn");
//resetBtn.addEventListener("click", resetSensorData);


setInterval(fetchData,1000);

