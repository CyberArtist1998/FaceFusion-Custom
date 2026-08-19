@echo off
cd /d "D:\MyWorld-Sync\011-AI\FaceFusion"
venv\Scripts\python.exe facefusion.py headless-run ^
  -s "D:/MyWorld-Sync/051-GraphicDesign/002-MertydomPosters/پهپاد - ناخداسوم خلبان - محمدصادق توانی بلیانی/photo_2026-04-08_22-17-58.jpg" ^
  -t "D:/MyWorld-Sync/051-GraphicDesign/002-MertydomPosters/Raw Pictures/Gemini_Generated_Image_pdpbtkpdpbtkpdpb.png" ^
  --processors deep_swapper ^
  --output-path "D:/MyWorld-Sync/051-GraphicDesign/002-MertydomPosters/final_output.png"