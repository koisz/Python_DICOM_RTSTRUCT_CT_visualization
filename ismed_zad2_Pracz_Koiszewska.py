import tkinter as tk
from tkinter import *
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
import numpy as np
import pydicom
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon


class AppDICOM:
    """
    Klasa AppDICOM pozwalająca na wczytwanie i wizualizację wybranych struktur RTSTRUCT na obrazach z CT.

    Atrybuty:
        root (tkinter.Tk): Główne okno aplikacji.
        DICOMCT (pydicom.dataset.FileDataset): Wczytywwany plik z CT w formacie DICOM.
        DICOMRTSTRUCT (pydicom.dataset.FileDataset): Wczytywany plik z RTSTRUCT w formacie DICOM.
        figure (matplotlib.figure.Figure): Figura używana do wizualizacji obrazów i struktur.
        axes (matplotlib.axes._axes.Axes): Elementy dodawane do wykresu.
        canvasWidget (tkinter.Canvas): Widżet do umieszczenia płótna wizualizującego.
        canvas (matplotlib.backends.backend_tkagg.FigureCanvasTkAgg): Płótno do wyświetlania obrazów CT i struktur RTSTRUCT.
        ROINames (list): Lista dostępnych ROI dla danego obrazu CT.
        selectedROIs (list): Lista wybranych ROI przez użytkownika.
    """

    def __init__(self):
        """
         Inicjalizacja obiektu AppDICOM.
        """
        self.root = tk.Tk()
        self.root.title("CT + RTSTRUCT Viewer")
        self.DICOMCT = None
        self.DICOMRTSTRUCT = None
        self.figure = None
        self.axes = None
        self.canvasWidget = None
        self.canvas = None
        self.ROINames = []
        self.selectedROIs = []
        self.createWigets()
        self.root.mainloop()

    def createWigets(self):
        """
        Utworzenie i konfiguracja elementów GUI.
        """
        buttonFrame = Frame(self.root)
        button1 = Button(buttonFrame, text=" Load CT ", command=self.loadCT)
        button2 = Button(buttonFrame, text=" Load RTSTRUCT ", command=self.loadRTSTRUCT)
        button3 = Button(buttonFrame, text=" Select ROI ", command=self.selectROI)
        button4 = Button(buttonFrame, text=" Visualize ", command=self.visualize)

        button1.pack(side=TOP, padx=5, pady=5)
        button2.pack(side=TOP, padx=5, pady=5)
        button3.pack(side=TOP, padx=5, pady=5)
        button4.pack(side=TOP, padx=5, pady=5)

        buttonFrame.pack(side=RIGHT, padx=5, pady=5)

        self.figure, self.axes = plt.subplots()
        self.axes.axis('off')
        self.axes.text(0.5, 0.5, "Load DICOM files", ha='center', va='center', fontsize=13)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvasWidget = self.canvas.get_tk_widget()
        self.canvasWidget.pack(side=TOP, fill=tk.BOTH, expand=YES)

    def loadCT(self):
        """
        Funkcja wczytująca plik CT, sprawdzająca poprawność wybranej ścieżki pliku.
        """
        CTFile = filedialog.askopenfilename(title="Choose CT file", filetypes=[("DICOM files", "*.dcm")])
        if CTFile:
            self.DICOMCT = pydicom.dcmread(CTFile)
            if self.DICOMCT.Modality != "CT":
                print(f"This is not a DICOM CT file type.")
                messagebox.showwarning("WARNING!", "This is not a DICOM CT file type.")
                self.DICOMCT = None
        else:
            print("File selection has been canceled.")

    def loadRTSTRUCT(self):
        """
        Funkcja wczytująca plik RTSTRUCT, sprawdzająca poprawność wybranej ścieżki pliku.
        """
        RTSTRUCTFile = filedialog.askopenfilename(title="Choose RTSTRUCT file", filetypes=[("DICOM files", "*.dcm")])
        if RTSTRUCTFile:
            self.DICOMRTSTRUCT = pydicom.dcmread(RTSTRUCTFile)
            if self.DICOMRTSTRUCT.Modality != "RTSTRUCT":
                print(f"This is not a DICOM RTSTRUCT file type.")
                messagebox.showwarning("WARNING!", "This is not a DICOM RTSTRUCT file type.")
                self.DICOMRTSTRUCT = None
        else:
            print("File selection has been canceled.")

    def getROI(self):
        """
        Funkcja pobierająca ROI z pliku RTSTRUCT.
        :return: Zwraca listę pobranych ROI.
        """
        rois = []
        if "StructureSetROISequence" in self.DICOMRTSTRUCT:
            for roiContour in self.DICOMRTSTRUCT.StructureSetROISequence:
                roiNames = roiContour.ROIName
                self.ROINames.append(roiNames)

        counter = 0
        if "ROIContourSequence" in self.DICOMRTSTRUCT:
            for roiContour in self.DICOMRTSTRUCT.ROIContourSequence:
                roiName = roiContour.get("ROIName", f"{self.ROINames[counter]}")
                counter += 1

                if "ContourSequence" in roiContour:
                    for i in roiContour.ContourSequence:
                        if self.checkContour(i):
                            rois.append(roiName)
                            break

        else:
            raise ValueError("No RTSTRUCT file has been found. Please load RTSTRUCT file.")

        return rois

    def selectROI(self, roiSelection=None):
        """
        Funkcja pozwalająca na wybór ROI przez użytkownika.
        :param roiSelection: Okno pozwalające na wybór ROI.
        """
        if self.DICOMCT is None and self.DICOMRTSTRUCT is None:
            messagebox.showwarning("WARNING!", "No CT and RTSTRUCT files have been found. Please load files.")
            return
        if self.DICOMCT is None:
            messagebox.showwarning("WARNING!", "No CT file has been found. Please load CT file.")
            return
        if self.DICOMRTSTRUCT is None:
            messagebox.showwarning("WARNING!", "No RTSTURCT file has been found. Please load RTSTRUCT file.")
            return

        try:
            rois = self.getROI()
        except ValueError as e:
            messagebox.showwarning("WARNING!", str(e))
            return

        roiSelection = tk.Toplevel(self.root)
        roiSelection.title("SELECT ROI")
        roiList = Listbox(roiSelection, selectmode=tk.MULTIPLE, exportselection=0, height=len(rois))

        for i in rois:
            roiList.insert(END, i)

        tk.Label(roiSelection, text="Select ROI: ").pack()
        roiList.pack()

        def ok():
            selectedData = roiList.curselection()
            self.selectedROIs = [rois[i] for i in selectedData]
            roiSelection.destroy()

        OKButton = tk.Button(roiSelection, text="OK", command=ok)
        OKButton.pack()

    def checkContour(self, contourItem):
        """
        Funkcja sprawdzająca poprawność odniesienia konturu do wczytywanego pliku CT.
        :param contourItem: Kontur, który jest sprawdzany.
        return: Zwraca True lub False w zależności od poprawności odniesienia do pliku.
        """
        return contourItem.ContourImageSequence[0].ReferencedSOPInstanceUID == self.DICOMCT.SOPInstanceUID

    def drawContour(self, aX, contourData):
        """
        Funkcja rysująca wybrany kontur.
        :param aX: Osie do rysowania.
        :param contourData: Dane konturu, który jest rysowany.
        """
        polygon = Polygon(contourData[:, :2], edgecolor='m', facecolor='none')
        aX.add_patch(polygon)

    def drawROI(self, aX):
        """
        Funkcja rysująca wybrane ROI na obrazie CT.
        :param aX: Osie do rysownaia.
        """
        counter = 0
        for roiContour in self.DICOMRTSTRUCT.ROIContourSequence:
            roiName = roiContour.get("ROIName", f"{self.ROINames[counter]}")
            counter += 1

            if roiName in self.selectedROIs and "ContourSequence" in roiContour:
                for i in roiContour.ContourSequence:
                    if self.checkContour(i):
                        contourData = np.array(i.ContourData).reshape(-1, 3)
                        self.drawContour(aX, contourData)

    def calculateImageDimensions(self, DICOM):
        """
        Funkcja obliczająca wymiary obrazu CT.
        :param DICOM: Obiekt reprezentujący obraz CT.
        :return: Obliczone wartości wymiarów obrazu.
        """
        rows = DICOM.Rows
        columns = DICOM.Columns
        pixelX = DICOM.PixelSpacing[0]
        pixelY = DICOM.PixelSpacing[1]

        x1 = DICOM.ImagePositionPatient[0]
        x2 = x1 + pixelX * rows
        y1 = DICOM.ImagePositionPatient[1]
        y2 = y1 + pixelY * columns

        return x1, x2, y1, y2

    def visualize(self):
        """
        Funkcja wizualizująca wybrane ROI na obrazie CT.
        """
        if self.DICOMCT is None or self.DICOMRTSTRUCT is None or not self.selectedROIs:
            messagebox.showwarning("WARNING!", "Please load CT, RTSTRUCT, and select ROIs first.")
            return

        self.axes.clear()
        self.figure.clf()

        aX = self.figure.add_subplot(1, 1, 1)
        DICOMImage = self.DICOMCT.pixel_array

        x1, x2, y1, y2 = self.calculateImageDimensions(self.DICOMCT)
        aX.imshow(DICOMImage, cmap="gray", extent=(x1, x2, y2, y1))
        self.drawROI(aX)

        aX.set_title(f"Selected ROIs: {', '.join(self.selectedROIs)}")
        aX.axis('off')
        self.canvas.draw()

if __name__ == "__main__":
    app = AppDICOM()
