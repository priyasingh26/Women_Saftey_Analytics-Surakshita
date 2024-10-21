// let map;
let safeAreasMap;

var map = L.map("map").setView([51.505, -0.09], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

var hospitalMarkers = [];
var policeMarkers = [];
var crowdedAreaMarkers = [];
var userLocation = null;
var currentRoute = null;
var userMarker;

// Shared location update functionality for mobile and desktop
function updateUserLocation(location) {
  var lat = location.coords.latitude;
  var lon = location.coords.longitude;
  userLocation = [lat, lon];


  if (!userMarker) {
    userMarker = L.marker(userLocation)
      .addTo(map)
      .bindPopup("You are here!")
      .openPopup();
  } else {
    userMarker.setLatLng(userLocation);
  }

  map.setView(userLocation, 13);
  fetchNearbyLocations(userLocation);
}

// Watch location for mobile, or fetch once for desktop
function trackUserLocation() {
  if (navigator.geolocation) {
    if (window.innerWidth <= 768) {
      // Mobile: continuous tracking
      navigator.geolocation.watchPosition(updateUserLocation, handleError, {
        enableHighAccuracy: true,
        // timeout: 5000,
        // maximumAge: 0,
      });
    } else {
      // Desktop: fetch once
      navigator.geolocation.getCurrentPosition(
        updateUserLocation,
        handleError,
        {
          enableHighAccuracy: true,
        }
      );
    }
  } else {
    alert("Geolocation is not supported by this browser.");
  }
}

function fetchNearbyLocations(location, radius = 1000) {
  var lat = location[0];
  var lon = location[1];

  // Clear existing markers
  clearMarkers();

  // Fetch nearby hospitals
  fetch(
    `https://overpass-api.de/api/interpreter?data=[out:json];node["amenity"="hospital"](around:${radius},${lat},${lon});out;`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.elements && data.elements.length > 0) {
        data.elements.forEach((item) => {
          var latLng = [item.lat, item.lon];
          var marker = L.marker(latLng, { icon: hospitalIcon })
            .addTo(map)
            .bindPopup(
              createPopup(item.tags.name ? item.tags.name : "Hospital", latLng)
            );
          hospitalMarkers.push(marker);
        });
      } else {
        console.log("No hospitals found in the response.");
      }
    })
    .catch((error) => console.error("Error fetching hospitals:", error));

  // Fetch nearby police stations
  fetch(
    `https://overpass-api.de/api/interpreter?data=[out:json];node["amenity"="police"](around:${radius},${lat},${lon});out;`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.elements && data.elements.length > 0) {
        data.elements.forEach((item) => {
          var latLng = [item.lat, item.lon];
          var marker = L.marker(latLng, { icon: policeIcon })
            .addTo(map)
            .bindPopup(
              createPopup(
                item.tags.name ? item.tags.name : "Police Station",
                latLng
              )
            );
          policeMarkers.push(marker);
        });
      } else {
        console.log("No police stations found in the response.");
      }
    })
    .catch((error) => console.error("Error fetching police stations:", error));

  // Fetch nearby crowded areas (parks and malls)
  fetch(
    `https://overpass-api.de/api/interpreter?data=[out:json];node["leisure"="park"](around:${radius},${lat},${lon});out;`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.elements && data.elements.length > 0) {
        data.elements.forEach((item) => {
          var latLng = [item.lat, item.lon];
          var marker = L.marker(latLng, { icon: parkIcon })
            .addTo(map)
            .bindPopup(
              createPopup(item.tags.name ? item.tags.name : "Park", latLng)
            );
          crowdedAreaMarkers.push(marker);
        });
      } else {
        console.log("No parks found in the response.");
      }
    })
    .catch((error) => console.error("Error fetching parks:", error));

  fetch(
    `https://overpass-api.de/api/interpreter?data=[out:json];node["shop"="mall"](around:${radius},${lat},${lon});out;`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.elements && data.elements.length > 0) {
        data.elements.forEach((item) => {
          var latLng = [item.lat, item.lon];
          var marker = L.marker(latLng, { icon: mallIcon })
            .addTo(map)
            .bindPopup(
              createPopup(
                item.tags.name ? item.tags.name : "Shopping Center",
                latLng
              )
            );
          crowdedAreaMarkers.push(marker);
        });
      } else {
        console.log("No shopping centers found in the response.");
      }
    })
    .catch((error) => console.error("Error fetching shopping centers:", error));
}

function clearMarkers() {
  hospitalMarkers.forEach((marker) => map.removeLayer(marker));
  policeMarkers.forEach((marker) => map.removeLayer(marker));
  crowdedAreaMarkers.forEach((marker) => map.removeLayer(marker));
  hospitalMarkers = [];
  policeMarkers = [];
  crowdedAreaMarkers = [];
  if (currentRoute) {
    map.removeControl(currentRoute);
    currentRoute = null;
  }
}

safeAreasMap = L.map("safe-areas-map").setView([51.505, -0.09], 13); // Set initial coordinates and zoom level

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(safeAreasMap);

function createPopup(name, latLng) {
  return `<div>
            <p>${name}</p>
            <button onclick="getDirections(${latLng[0]}, ${latLng[1]})">Get Directions</button>
        </div>`;
}

function getDirections(lat, lon) {
  if (!userLocation) {
    alert("User location not available.");
    return;
  }

  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  currentRoute = L.Routing.control({
    waypoints: [L.latLng(userLocation[0], userLocation[1]), L.latLng(lat, lon)],
    createMarker: function () {
      return null;
    },
    routeWhileDragging: true,
  }).addTo(map);
}

function toggleMarkers(markerArray, iconType) {
  if (iconType === "hospital") {
    hospitalMarkers.forEach((marker) => {
      if (map.hasLayer(marker)) {
        map.removeLayer(marker);
      } else {
        marker.addTo(map);
      }
    });
  } else if (iconType === "police") {
    policeMarkers.forEach((marker) => {
      if (map.hasLayer(marker)) {
        map.removeLayer(marker);
      } else {
        marker.addTo(map);
      }
    });
  } else if (iconType === "crowded") {
    crowdedAreaMarkers.forEach((marker) => {
      if (map.hasLayer(marker)) {
        map.removeLayer(marker);
      } else {
        marker.addTo(map);
      }
    });
  }
}

var hospitalIcon = L.icon({
  iconUrl: "../static/hospital.png", // Replace with your hospital icon URL
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

var policeIcon = L.icon({
  iconUrl: "../static/policeman.png", // Replace with your police icon URL
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

var parkIcon = L.icon({
  iconUrl: "../static/people-group-solid.svg", // Replace with your park icon URL
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

var mallIcon = L.icon({
  iconUrl: "../static/people-group-solid.svg", // Replace with your mall icon URL
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

// Handle error for geolocation
function handleError(error) {
  alert("Unable to retrieve your location. Error code: " + error.code);
}

document.getElementById("getLocationBtn").onclick = trackUserLocation;

document.getElementById("toggleHospitals").onclick = function () {
  toggleMarkers(hospitalMarkers, "hospital");
};

document.getElementById("togglePolice").onclick = function () {
  toggleMarkers(policeMarkers, "police");
};

document.getElementById("toggleCrowdedAreas").onclick = function () {
  toggleMarkers(crowdedAreaMarkers, "crowded");
};

// Event listener for radius change
document.getElementById("radiusSelect").addEventListener("change", function () {
  currentRadius = this.value;
  if (userLocation) {
    fetchNearbyLocations(userLocation, currentRadius);
  }
});

// Initialize the maps after the window has loaded

// Function to call a contact
function callContact(phoneNumber) {
  window.location.href = `tel:${phoneNumber}`;
}

function playAlertSound() {
  const alertSound = document.getElementById("alert-sound");
  alertSound.play();
}

function showAlertOverlay() {
  document.getElementById("alert-overlay").style.display = "block";
}
function hideAlertOverlay() {
  document.getElementById("alert-overlay").style.display = "none";
}

// Example event listener for emergency alert button
document.addEventListener("DOMContentLoaded", function () {
  const emergencyButton = document.getElementById("emergency-alert");

  // Function to start real-time location tracking
  function startLocationTracking() {
    if (navigator.geolocation) {
      navigator.geolocation.watchPosition(
        function (position) {
          const userLocation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };

          // Send real-time location to the backend
          fetch("/send-location", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ location: userLocation }),
          })
            .then((response) => response.json())
            .then((data) => {
              console.log("Location updated:", data);
            });
        },
        function (error) {
          console.error("Error getting location:", error);
        },
        {
          enableHighAccuracy: true, // Use GPS for more accurate location
          maximumAge: 10000, // Reuse location data for up to 10 seconds
          timeout: 10000, // Timeout after 10 seconds
        }
      );
    } else {
      console.error("Geolocation is not supported by this browser.");
    }
  }

  if (emergencyButton) {
    emergencyButton.addEventListener("click", function () {
      // Start real-time location tracking when emergency is triggered
      startLocationTracking();

      // Play alert sound and show the alert overlay
      playAlertSound();
      showAlertOverlay();
      setTimeout(() => {
        hideAlertOverlay();
      }, 30000);

      // Send initial emergency alert
      fetch("/emergency-alert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ alert: true }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Emergency alert triggered:", data);
        });
    });
  }
});

// Function to update analytical data
function updateAnalyticalData() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        fetch(`/user_counts?latitude=${latitude}&longitude=${longitude}`)
          .then((response) => response.json())
          .then((data) => {
            const maleCount = data.male_count;
            const femaleCount = data.female_count;
            const ratio =
              femaleCount > 0 ? (maleCount / femaleCount).toFixed(2) : "N/A";

            document.getElementById("male-count").innerText = maleCount;
            document.getElementById("female-count").innerText = femaleCount;
            document.getElementById("ratio").innerText = ratio;
          })
          .catch((error) =>
            console.error("Error fetching user counts:", error)
          );
      },
      (error) => {
        console.error("Error getting location:", error);
      }
    );
  } else {
    alert("Geolocation is not supported by this browser.");
  }
}

// Update analytical data every 10 seconds
setInterval(updateAnalyticalData, 10000);

// Initial fetch
updateAnalyticalData();

// Function to update real-time alerts
// function updateAlerts() {
//     fetch('/alerts')
//         .then(response => response.json())
//         .then(data => {
//             const alertsContainer = document.getElementById('alerts-container');
//             alertsContainer.innerHTML = ''; // Clear existing alerts

//             data.alerts.forEach(alert => {
//                 const alertDiv = document.createElement('div');
//                 alertDiv.className = 'alert';
//                 alertDiv.innerText = alert.message;
//                 alertsContainer.appendChild(alertDiv);
//             });
//         })
//         .catch(error => console.error('Error fetching alerts:', error));
// }

// Update alerts every 30 seconds
// setInterval(updateAlerts, 30000);

// Initial fetch
// updateAlerts();

// Dark mode toggle
document
  .getElementById("dark-mode-toggle")
  .addEventListener("click", function () {
    document.body.classList.toggle("dark-mode");
    const icon = this.querySelector("i");
    if (document.body.classList.contains("dark-mode")) {
      icon.classList.remove("fa-moon");
      icon.classList.add("fa-sun");
    } else {
      icon.classList.remove("fa-sun");
      icon.classList.add("fa-moon");
    }
  });
