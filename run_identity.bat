@echo off
cd /d "D:\MyWorld-Sync\011-AI\FaceFusion"
call venv\Scripts\activate.bat
python "D:/MyWorld-Sync/051-GraphicDesign/002-MertydomPosters/scripts/ff_identity.py" %*
deactivate
