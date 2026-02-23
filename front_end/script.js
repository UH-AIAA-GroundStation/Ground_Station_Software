async function fetchData() {
  try {
    // Await the fetch call and get the Response object
    const response = await fetch("http://127.0.0.1:8000/read_data");

    // Check if the request was successful
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Await the response.json() call to parse the body as JSON
    const data = await response.json();

    // Return the parsed data
    console.log(data);
  } catch (error) {
    // Handle any errors that occurred during the fetch operation
    console.error("Could not fetch data:", error);
  }
}

fetchData();