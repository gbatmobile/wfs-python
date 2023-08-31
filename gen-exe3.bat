pyinstaller --distpath . --onefile wfs_extractor_v3.py
rmdir build /S /Q
del *.spec
rmdir __pycache__ /S /Q