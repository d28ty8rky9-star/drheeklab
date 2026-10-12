"""Display the eight supplied icons from their original reference sheet.

The source image stays unchanged; pixmap regions exclude printed captions.
"""
from importlib.resources import files
from PySide6.QtGui import QPixmap,QIcon

# Coordinates on the user's 1280 x 853 reference, in navigation order.
REGIONS=((51,98,263,261),(354,98,263,261),(662,98,263,261),(967,98,264,261),
         (51,445,263,261),(354,445,263,261),(662,445,263,261),(967,445,264,261))

def menu_icons():
    resources=files('drheeklab').joinpath('assets')
    for name in ('menu-referencia.png','menu-referencia.jpg','menu-referencia.jpeg'):
        resource=resources.joinpath(name)
        if not resource.is_file():continue
        sheet=QPixmap(str(resource))
        if sheet.isNull():continue
        width,height=sheet.width(),sheet.height()
        return [QIcon(sheet.copy(round(x*width/1280),round(y*height/853),round(w*width/1280),round(h*height/853)))
                for x,y,w,h in REGIONS]
    return [QIcon() for _ in REGIONS]
