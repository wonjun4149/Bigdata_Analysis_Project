<?php
$S_N = $_GET['S_N'];
$progress_file = sys_get_temp_dir() . "/progress_$S_N.json";

if (file_exists($progress_file)) {
    $progress = json_decode(file_get_contents($progress_file), true);
    echo json_encode($progress);
} else {
    echo json_encode(['progress' => 0]);
}
?>
