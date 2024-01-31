document.addEventListener('DOMContentLoaded', function() {
    initMap();
});
var mymap;
var searchTimeout;
var lastCityValue = ''; // Memorizza l'ultimo valore del campo "city"
var lastCountryCode = ''; // Memorizza l'ultimo valore del campo "countrycode"
var marker;



function initMap() {
    mymap = L.map('map').setView([41.8719, 12.5674], 5); // Imposta la vista iniziale della mappa
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mymap); // Aggiunge un layer di OpenStreetMap 
    // var openWeatherMapLayer = L.tileLayer('https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=109a274e47fac26e28be9c3d15bbc8e6', {
    //   attribution: '© OpenWeatherMap'
    // }).addTo(mymap);
}

function sendData() {
    var form = document.getElementById("weatherForm");
    var formData = new FormData(form);
    fetch('/sendRequest', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            // Handle success (if needed)
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle error (if needed)
        });
}


async function searchWeather() {

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async() => {
        const sessionIsValid = await checkSession();
        if (sessionIsValid) {
            var city = document.getElementById('city').value.trim();
            var countrycode = document.getElementById('countrycode').value.trim();
            var minTemp = parseFloat(document.getElementById('minTemp').value);
            var maxTemp = parseFloat(document.getElementById('maxTemp').value);
            var rain = parseFloat(document.getElementById('rain').value);
            var snow = document.getElementById('snow').value;

            if (city === '' && countrycode === '') {
                if (marker) {
                    mymap.removeLayer(marker);
                }
                // Resetta la mappa quando il campo "city" è vuoto
                mymap.setView([41.8719, 12.5674], 5);
                //return; // Esce dalla funzione senza effettuare ulteriori richieste
            } else {
                if (marker) {
                    mymap.removeLayer(marker);
                }
                // Aggiorna la posizione della mappa in base alla città (usa API di geocoding)
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${city}&countrycodes=${countrycode}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);
                        if (data.length > 0) {
                            var lat = parseFloat(data[0].lat);
                            var lon = parseFloat(data[0].lon);




                            mymap.setView([lat, lon], 10); // Imposta la vista della mappa sulla posizione della città
                            // L.marker([lat, lon]).addTo(mymap); // Aggiunge un marker sulla posizione
                            //const marker = L.marker([lat, lon]).addTo(mymap);
                            // Imposta il popup con autoClose su false
                            //const popup = L.popup({
                            //     autoClose: false
                            //  })
                            //  .setContent(`Latitudine: ${lat}°C<br>${lon}`);

                            // Associa il popup al marcatore e apri il popup
                            // marker.bindPopup(popup).openPopup();
                            // marker.bindPopup(`Temperatura: ${temperature}°C<br>${description}`).openPopup();

                        }
                    });


                fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city},${countrycode}&lang=it&appid=109a274e47fac26e28be9c3d15bbc8e6`)
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);

                        const coordinates = data.coord;

                        let rain_content = '';
                        let snow_content = '';
                        // Estrai i dati meteorologici da 'data'
                        const description = data.weather[0].description;
                        const temperature = (data.main.temp - 273.15).toFixed(2); // Converte da Kelvin a Celsius
                        const tMax = (data.main.temp_max - 273.15).toFixed(2);
                        const tMin = (data.main.temp_min - 273.15).toFixed(2);
                        if (data.rain && data.rain['1h']) {
                            const Rain = data.rain['1h'];
                            rain_content = `<br>Pioggia:${Rain}`;
                        }
                        if (data.snow && data.snow['1h']) {
                            const Snow = data.snow['1h'];
                            snow_content = `<br>Neve:${Snow}`;
                        }


                        // Accesso alle coordinate lon e lat 
                        const lat = parseFloat(coordinates.lat);
                        const lon = parseFloat(coordinates.lon);


                        console.log("lat: ", lat, "lon: ", lon);

                        // Aggiungi un marker alla posizione specificata sulla mappa
                        marker = L.marker([lat, lon]).addTo(mymap);
                        // Imposta il popup con autoClose su false
                        const popup = L.popup({
                                autoClose: false
                            })
                            .setContent(`${description}<br>Temperatura:${temperature}°C<br>Temperatura massima:${tMax}°C<br>Temperatura minima:${tMin}°C${rain_content}${snow_content}`);

                        // Associa il popup al marcatore e apri il popup
                        marker.bindPopup(popup).openPopup();




                    });

            }
        }

    }, 500);
}
// questo serve a fare in modo che quando inserisco il nome e il paese la mappa si sposti e si posizioni nella località digitata
const cityInput = document.getElementById('city');
const countryInput = document.getElementById('countrycode');


cityInput.addEventListener('input', searchWeather);
countryInput.addEventListener('input', searchWeather);



async function checkSession() {
    // Verifica la sessione utilizzando una richiesta asincrona (puoi utilizzare AJAX o Fetch API)
    try {
        const response = await fetch('/check_session');
        if (response.status !== 200) {
            // La sessione è scaduta, reindirizza alla pagina di login
            window.location.href = '/login';
            return false;
        }
        // La sessione è valida, permetti l'invio del form
        return true;
    } catch (error) {
        console.error('Errore nella verifica della sessione:', error);
        return false;
    }
}