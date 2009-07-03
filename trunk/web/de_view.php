<html>
<meta http-equiv="refresh" content="15">

<body>

<?php
    $case_id = $_GET['case_id'];
    if (empty($case_id)) {
        die();
    }
?>

<?php // Change physio.gif to ecg plot ?>
<center><img src="uploads/<?php echo $case_id; ?>/latest.jpg" alt="Physio Data" /> </center>

</body>
</html>
