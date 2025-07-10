from UIClassTeiDataAcqNature import App
from backpacklib import backpack
import os


os.chdir(os.path.dirname(os.path.abspath(__file__)))


app = App(backpack)
if __name__ == "__main__":
    app.mainloop()


















