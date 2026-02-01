from tkinter import Tk

from .ui import ReportApp


def main():
    root = Tk()
    ReportApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
