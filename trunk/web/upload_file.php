<?php

if (empty($_POST['case_id'])) {
    echo -3;
    die();
}


$target_path = "uploads/" .$_POST['case_id']. "/";
$FUP = $_FILES["file"];

if (empty($_POST['sequence_id'])){
    $target_path = $IMAGEPATH;
}


if ($FUP["error"] > 0) {
    echo -1;
}
else {
    if (!is_dir($target_path)) {
        echo $target_path;
        mkdir($target_path);
    } 
    $target_path = $target_path . basename( $FUP['name']); 
//    $target_path = $target_path . "latest.jpg";
    
    // Do overwrite check before this
    if(move_uploaded_file($FUP['tmp_name'], $target_path)) {
        echo 0;
        exec("python edfparser.py -c config.conf" . $target_path);
    } else {
        echo -2;
    }

}
?>
