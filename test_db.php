<?php
// Fichier: test_db.php

// On active l'affichage de TOUTES les erreurs pour le débogage
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

echo "<h1>Test de connexion à la base de données</h1>";

// --- Configuration (la même que dans get_data.php) ---
$db_host = 'localhost';
$db_name = 'sae24'; // Assurez-vous que c'est le bon nom
$db_user = 'sae24'; // Assurez-vous que c'est le bon utilisateur
$db_pass = 'leo'; // METTEZ VOTRE MOT DE PASSE

try {
    echo "<p>Tentative de connexion à la base de données '$db_name' avec l'utilisateur '$db_user'...</p>";
    
    // Connexion à la BDD avec PDO
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8", $db_user, $db_pass);
    
    // Si on arrive ici, la connexion a réussi !
    echo "<p style='color:green; font-weight:bold;'>Connexion réussie !</p>";

    // Maintenant, testons une requête simple
    echo "<p>Tentative de compter les lignes dans la table 'positions'...</p>";
    
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM positions");
    $stmt->execute();
    $rowCount = $stmt->fetchColumn(); // Récupère la première colonne du premier résultat

    echo "<p style='color:green; font-weight:bold;'>Succès ! Nombre de positions dans la table : " . $rowCount . "</p>";


} catch (PDOException $e) {
    // En cas d'erreur, on affiche un message très clair
    echo "<h2 style='color:red;'>ÉCHEC DE LA CONNEXION</h2>";
    echo "<p style='color:red; font-family:monospace; background-color:#f1f1f1; padding:10px;'>";
    echo "Message d'erreur : " . $e->getMessage();
    echo "</p>";
}
?>
