# Ground_Station_Software
Ground station software 
<br><br>

#  Coding standard AIAA:

  -  snake_case() function name
  -  Comment on code
  -  Write as few line as possible
  -  Avoid Deep nesting (avoid double loop function that increases time complexity)
  -  Avoid long lines
  -  Explicit naming (no i,j,etc... Ex: time)
  -  ReadMe for your code


  # Build .exe 
  pyinstaller --noconfirm --onefile --windowed `
    --add-data "Entry_Layout.ui;." `
    --add-data "Ground_Station_App_Layout.ui;." `
    --add-data "cropped-aiaaweblogo.png;." `
    entry.py