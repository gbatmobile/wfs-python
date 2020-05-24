echo "Por enquanto cxfreeze nao suporta espacos nos nomes de pastas. Usando \tmp"

set PWD=%cd%
mkdir c:\tmp\wfs0.4

copy WFS04_Extractor_v2.py c:\tmp\wfs0.4

cd C:\tools\Python36-64\Scripts
c:

mkdir "%PWD%\exe"
python cxfreeze  c:\tmp\wfs0.4\WFS04_Extractor_v2.py --target-dir "%PWD%\exe"
cd "%PWD%\exe"