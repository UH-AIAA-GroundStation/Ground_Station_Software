 import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Declare the chart dimensions and margins.
const width = 575;
const height = 300;
const marginTop = 5;
const marginRight = 20;
const marginBottom = 30;
const marginLeft = 40;



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
altSvg.append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(altX));

// 4. Add Y-axis (changed to axisLeft)
altSvg.append("g")
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
tempSvg.append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(tempX));

// 4. Add Y-axis (changed to axisLeft)
tempSvg.append("g")
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
gpsSvg.append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(d3.axisBottom(gpsX));

// 4. Add Y-axis (changed to axisLeft)
gpsSvg.append("g")
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
    const altData = data.altitude.timestamps.map((t, i) => ({
        time: t,
        val: data.altitude.values[i]
    }));

    const tempData = data.temperature.timestamps.map((t, i) => ({
        time: t,
        val: data.temperature.values[i]
    }));

    const gpsData = data.gps.x.map((a, b) => ({
        gX: a,
        gY: data.gps.y[b]
    }));

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

setInterval(fetchData, 1000);

