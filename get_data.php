<?php
header('Content-Type: application/json');

// --- Configuration de la base de données ---
$db_host = 'localhost';
$db_name = 'sae24'; // Ou sae24_db, selon ce que vous utilisez
$db_user = 'sae24'; // Ou sae24_user
$db_pass = 'leo'; // METTEZ VOTRE VRAI MOT DE PASSE

try {
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8", $db_user, $db_pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // On récupère les 50 dernières positions pour le tracé
    $stmt = $pdo->prepare("SELECT pos_x, pos_y, timestamp FROM positions ORDER BY timestamp DESC LIMIT 50");
    $stmt->execute();
    
    // On inverse le tableau pour avoir le plus ancien en premier et le plus récent en dernier
    $positions = array_reverse($stmt->fetchAll(PDO::FETCH_ASSOC));
    
    // Reformater les données pour le JavaScript
    $output = [];
    foreach ($positions as $row) {
        $output[] = [
            'x' => (float)$row['pos_x'],
            'y' => (float)$row['pos_y'],
            'time' => $row['timestamp']
        ];
    }
    
    echo json_encode($output);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Erreur de connexion à la base de données: ' . $e->getMessage()]);
}
?>
