document.addEventListener("DOMContentLoaded", function() {
    var userEmail = document.getElementById('current_user_email');

    if (userEmail) {
        var user_email = userEmail.value;

        fetch(`/get_subscriptions/${encodeURIComponent(user_email)}`)
            .then(onResponse)
            .then(onData)
            .catch(onError);

        console.log("Valore email:", user_email);
        console.log("Sto facendo la richiesta");
    } else {
        console.error("L'elemento con l'ID 'current_user_email' non è stato trovato.");
    }
});

function onResponse(response) {
    if (!response.ok) {
        throw new Error(`Errore nella richiesta: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

function onData(json) {
    console.log("Ritorno della richiesta");
    console.log(json);

    const container = document.querySelector("#MySubscriptions");
    container.innerHTML = ""; // Pulisce il contenuto del container prima di aggiungere nuovi elementi

    const createSubtitle = (text) => {
        const subtitle = document.createElement("p");
        subtitle.textContent = text;
        subtitle.classList.add("text-align-center", "text-muted", "div-subtitle");
        return subtitle;
    };

    for (let i = 0; i < json.length; i++) {
        const sub_container = document.createElement("div");
        sub_container.id = json[i].id;
        sub_container.classList.add("dimension");

        const div = document.createElement("div");
        div.classList.add("div");

        const div2 = document.createElement("div");
        div2.classList.add("div-body");

        div2.appendChild(createSubtitle(`Sottoscrizione N°: ${json[i].id}`));
        div2.appendChild(createSubtitle(`Città: ${json[i].city}`));
        div2.appendChild(createSubtitle(`Paese: ${json[i].countrycode}`));
        div2.appendChild(createSubtitle(`Temperatura minima(C°): ${json[i].minTemp}`));
        div2.appendChild(createSubtitle(`Temperatura massima(C°): ${json[i].maxTemp}`));
        div2.appendChild(createSubtitle(`Quantità di pioggia(mm): ${json[i].rain}`));
        div2.appendChild(createSubtitle(`Presenza di neve: ${json[i].snow ? 'si' : 'no'}`));

        const button = document.createElement("div");
        button.classList.add("button");

        const removeButton = document.createElement("button");
        removeButton.classList.add("button1");

        const removeLink = document.createElement("a");
        removeLink.href = `http://my.previsioniweather.com:8080/delete/${encodeURIComponent(json[i].id)}`;

        const removeImage = document.createElement("img");
        removeImage.src = "http://127.0.0.1:3001/static/Images/delete.png";
        removeImage.classList.add("image");

        removeLink.appendChild(removeImage);
        removeButton.appendChild(removeLink);

        button.appendChild(removeButton);
        div2.appendChild(button);
        div.appendChild(div2);
        sub_container.appendChild(div);

        container.appendChild(sub_container);
    }
}

function onError(error) {
    console.error('Errore durante la richiesta fetch:', error);
}