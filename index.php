<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAÉ24 - Localisation de source sonore</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>SAÉ24 : Projet intégratif</h1>
        <p>Localiser une source sonore dans un environnement intérieur</p>
    </header>
    <div class="main-container">
        <section class="map-section">
            <h2>Visualisation en temps réel</h2>
            <div id="room-container"></div>
        </section>
        <section class="data-section">
            <h2>Les 4 dernières positions</h2>
            <table id="positions-table">
                <thead><tr><th>Position (x, y)</th><th>Timestamp</th></tr></thead>
                <tbody id="table-body"></tbody>
            </table>
        </section>
    </div>

    <script>
        // --- CONFIGURATION ---
        const GRID_SIZE = 16;
        const CONTAINER_SIZE_PX = 640;
        const CASE_SIZE_PX = CONTAINER_SIZE_PX / GRID_SIZE; 
        const CASE_SIZE_M = 0.5;

        // --- ÉLÉMENTS DU DOM ---
        const mapContainer = document.getElementById('room-container');
        const tableBody = document.getElementById('table-body');
        let lastKnownTimestamp = null;

        // --- FONCTION DE CONVERSION MÈTRES -> PIXELS (LA CLÉ DU PROBLÈME) ---
        function metersToPixelCoords(x_meters, y_meters) {
            // Le calcul doit être basé sur le nombre de cases depuis le bord.
            // Une case fait 0.5m.
            // L'indice 'i' de la case est x_meters / 0.5 - 0.5.
            // Ex: x=0.25 -> i = 0.5 - 0.5 = 0.
            // Ex: x=0.75 -> i = 1.5 - 0.5 = 1.
            const i = Math.round((x_meters / CASE_SIZE_M) - 0.5);
            const j = Math.round((y_meters / CASE_SIZE_M) - 0.5);

            // Le centre de la case (i) en pixels est : i * CASE_SIZE_PX + (demi-case en px).
            const pixel_x = i * CASE_SIZE_PX + (CASE_SIZE_PX / 2);
            const pixel_y = j * CASE_SIZE_PX + (CASE_SIZE_PX / 2);
            
            return { x: pixel_x, y: pixel_y };
        }
        
        // --- INITIALISATION ---
        const mics = [ { id: 1, x: 0.25, y: 0.25 }, { id: 2, x: 0.25, y: 7.75 }, { id: 3, x: 7.75, y: 7.75 } ];
        mics.forEach(mic => {
            const micElement = document.createElement('div');
            micElement.className = 'mic';
            const micPixels = metersToPixelCoords(mic.x, mic.y);
            micElement.style.left = `${micPixels.x}px`;
            micElement.style.top = `${micPixels.y}px`;
            mapContainer.appendChild(micElement);
        });

        // --- FONCTIONS DE MISE À JOUR ---
        function drawPoints(points) {
            document.querySelectorAll('.object-point').forEach(p => p.remove());
            const lastFourPoints = points.slice(-4);
            lastFourPoints.forEach((point, index) => {
                const pointElement = document.createElement('div');
                pointElement.className = 'object-point';
                const pixelCoords = metersToPixelCoords(point.x, point.y);
                pointElement.style.left = `${pixelCoords.x}px`;
                pointElement.style.top = `${pixelCoords.y}px`;
                pointElement.style.opacity = (index + 1) / lastFourPoints.length;
                if (index === lastFourPoints.length - 1) pointElement.classList.add('current-point');
                mapContainer.appendChild(pointElement);
            });
        }
        
        function updateTable(points) {
            tableBody.innerHTML = '';
            const lastFourPoints = points.slice(-4).reverse();
            if (lastFourPoints.length === 0) {
                 tableBody.innerHTML = '<tr><td colspan="2" style="text-align:center;">En attente de données...</td></tr>';
                 return;
            }
            lastFourPoints.forEach(point => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>(${point.x.toFixed(2)}, ${point.y.toFixed(2)})</td><td>${new Date(point.time).toLocaleTimeString('fr-FR')}</td>`;
                tableBody.appendChild(row);
            });
        }

        async function fetchDataAndUpdateUI() {
            try {
                const response = await fetch('get_data.php');
                if (!response.ok) return;
                const data = await response.json();
                if (!data || data.length === 0) return; 
                const latestPointTimestamp = data[data.length - 1].time;
                if (latestPointTimestamp !== lastKnownTimestamp) {
                    drawPoints(data);
                    updateTable(data);
                    lastKnownTimestamp = latestPointTimestamp;
                }
            } catch (error) { console.error('Erreur:', error); }
        }
        
        fetchDataAndUpdateUI();
        setInterval(fetchDataAndUpdateUI, 1000); 
    </script>
</body>
</html>
