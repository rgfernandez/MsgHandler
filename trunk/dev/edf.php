<!--< ?php-->
<!--$a = "test";-->
<!--$b = true;-->
<!--$c = 50;-->
<!--$d = 60.4;-->
<!---->
<!--$code = <<<EOD-->
<!--import php-->
<!---->
<!--a = php.var('a')-->
<!--b = php.var('b')-->
<!--c = php.var('c')-->
<!--d = php.var('d')-->
<!---->
<!--print a, b, c, d-->
<!--print a, d / c + b, a-->
<!--EOD;-->
<!---->
<!--py_eval($code);-->
<!--?>-->

<?php
    $p = new Python('edfviewer', 'EDF_File', 'ECGv2.edf');
    print $p->getEdfSignal();
?>