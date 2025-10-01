import tkinter as tk
from tkinter import ttk, filedialog # ladniejsze style i okno do wyboru plików
import wave # do czytania plików audio wav
import struct # konwersja bajtow na liczby
import matplotlib # wykresy
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import scipy.signal as signal # czesc biblioteki scipy do przetwarzania sygnalow


class EstymatorTempa:
    def __init__(self, root):
        self.root = root
        self.root.title("Estymator Tempa")
        self.root.geometry("900x400")

        # Dane audio do analizy
        self.plik_audio = None
        self.sample_rate = None
        self.nazwa = ""

        # Wyniki analizy
        self.sygnal_energii = [] # zrobione
        self.sygnal_dolne_pasmo_energii = [] # zrobione
        self.sygnal_gorne_pasmo_energii = [] # zrobione
        self.transienty_dolne_pasmo = [] # zrobione
        self.transienty_gorne_pasmo = [] # zrobione
        self.mozliwe_tempa = []
        self.bpm1 = 0
        self.bpm2 = 0
        self.bpm3 = 0
        self.ui()

    def ui(self):
        glowne_okno = ttk.Frame(self.root, padding="10")  # https://www.tutorialspoint.com/python/tk_frame.htm
        glowne_okno.pack(side="top", fill="both", expand=True)

        self.label_napis = ttk.Label(glowne_okno, text="Wybierz plik .wav do estymacji tempa utworu", font=("Helvetica", 14),
                                     padding="10")  # https://stackoverflow.com/questions/77546894/set-different-font-sizes-for-characters-within-a-tkinter-label-or-button-in-pyth
        self.label_napis.pack(fill="x")

        self.button = ttk.Button(glowne_okno, text="Wybierz plik .wav", command=self.wgraj_plik, padding="10")
        self.button.pack(side="top", fill="x")

        # Ramka dla text boxa i prawej strony
        pozioma_ramka = ttk.Frame(glowne_okno, padding="10")
        pozioma_ramka.pack(side="top", fill="both", expand=True)

        # LEWA STRONA - text box
        lewa_ramka = ttk.Frame(pozioma_ramka)
        lewa_ramka.pack(side="left", fill="both", expand=True)

        self.text = tk.Text(lewa_ramka, height=20, width=50, padx=10, pady=10)
        # dodac jeszcze scrollbar
        self.text.pack(fill="both", expand=True)

        # PRAWA STRONA - BPM
        prawa_ramka = ttk.Frame(pozioma_ramka, padding="10")
        prawa_ramka.pack(side="right", fill="y")

        self.label_bpm = ttk.Label(prawa_ramka, text="Estymowany BPM:", font=("", 14), padding=5)
        self.label_bpm.pack(anchor="n")

        self.label_bpm1 = ttk.Label(prawa_ramka, text="1. --- BPM (x razy powtórzeń)", font=("", 14), padding=5)
        self.label_bpm1.pack(anchor="n")

        self.label_bpm2 = ttk.Label(prawa_ramka, text="2. --- BPM (x razy powtórzeń)", font=("", 13), padding=5)
        self.label_bpm2.pack(anchor="n")

        self.label_bpm3 = ttk.Label(prawa_ramka, text="3. --- BPM (x razy powtórzeń)", font=("", 12), padding=5)
        self.label_bpm3.pack(anchor="n")

        self.label_info = ttk.Label(prawa_ramka, text="info: Powyżej znajduję się ranking \nnajbardziej prawdopodobnych BPM", font=("", 11), padding=5)
        self.label_info.pack(anchor="n")

        # https://www.tutorialspoint.com/python/tk_frame.htm
        # https://stackoverflow.com/questions/77546894/set-different-font-sizes-for-characters-within-a-tkinter-label-or-button-in-pyth
        # https://www.tutorialspoint.com/python/tk_text.htm

    def info(self, text):
        self.text.insert(tk.END, text + "\n")
        self.text.see(tk.END)

    def wgraj_plik(self):
        try:
            filepath = filedialog.askopenfilename(initialdir="/",
                                                  title = "Wybierz plik .wav do estymacji BPM",
                                                  filetypes=(("wav", "*.wav"),)) # https://www.youtube.com/watch?v=q8WDvrjPt0M
            self.info(filepath)
        except Exception as e:
            self.info(f"Wystąpił błąd podczas wybierania pliku: {e}")

        try:
            w = wave.open(filepath, 'r') # https://stackoverflow.com/questions/2060628/reading-wav-files-in-python
            self.sample_rate = w.getframerate() # https://stackoverflow.com/questions/43490887/check-audios-sample-rate-using-python
            self.info(f"Sample_rate: {self.sample_rate}")


            self.sample_width = w.getsampwidth()

            if self.sample_width == 2:
                wave_data = w.readframes(-1)
                self.info(f"Wczytano {len(wave_data)} bajtów")

                self.audio_data = []
                for i in range(0, len(wave_data), 2):
                    sample = struct.unpack("<h", wave_data[i:i + 2])[0]
                    self.audio_data.append(sample)

                self.info(f"ilosc probek: {len(self.audio_data)}")
                self.info(f"Losowe probki: {self.audio_data[12000000:12000059]}") # losowe próbki ze środka bardziej

                self.normalized_audio_data = self.normalizacja_audio(self.audio_data)

                self.start_analizy()

            else:
                self.info("Dźwięk nie ma szerokosci 16-bit")

        except Exception as e:
            self.info(f"Wystąpił błąd podczas otwierania pliku: {e}")

    def start_analizy(self):
        self.info("Startujemy analizę utowru.")

        # normalizujemy audio do 30k gzdie max to okolo 31.5k wiec jest to jakies -0.7 dB
        # https://stackoverflow.com/questions/41709257/how-to-change-the-plot-line-color-from-blue-to-black
        plt.figure(figsize = (20, 8))
        plt.plot(self.normalized_audio_data, color="#3333ff")
        plt.title("Znormalizowane audio")
        plt.xlabel("czas")
        plt.ylabel("Amplituda")
        plt.grid(True)
        plt.show()
        self.info("Stworozny wykres znormalizowanego sygnalu audio")

        # uzupełniamy liste energii i towrzymy plot do energii
        self.sygnal_energii = []
        for i in range(0, len(self.normalized_audio_data) - 1):
            self.sygnal_energii.append(abs(self.normalized_audio_data[i + 1] - (self.normalized_audio_data[i])))

        plt.figure(figsize = (20, 8))
        plt.plot(self.sygnal_energii, color="#9933ff")
        plt.title("Sygnał energii")
        plt.xlabel("czas")
        plt.ylabel("Energia")
        plt.grid(True)
        plt.show()
        self.info("Stworozny wykres znormalizowanej energii audio")

        # tworzymy pasmo 20hz - 80 hz - dla stopy i wykrywania kicka BAND PASS FILTER
        self.sygnal_dolne_pasmo_energii = []
        self.oblicz_pasmo_energii(self.normalized_audio_data, 20, 80, self.sample_rate, 2)

        # tworzymy pasmo 700hz - 12 000 hz - dla wykrywania perkusyjnych rzeczy
        self.sygnal_gorne_pasmo_energii = []
        self.oblicz_pasmo_energii(self.normalized_audio_data, 1000, 5000, self.sample_rate, 9)

        # tworzymy funkcje która obliczy z wzoru kwartyl trzeci lecz nie 0.75 tlyko jakieś okolo 0.9999
        self.Q3_low = self.znajdz_Q3(self.sygnal_dolne_pasmo_energii)
        self.znajdz_transienty(self.sygnal_dolne_pasmo_energii, self.transienty_dolne_pasmo, self.Q3_low)
        # self.transienty_dolne_pasmo
        self.Q3_high = self.znajdz_Q3(self.sygnal_gorne_pasmo_energii)
        self.znajdz_transienty(self.sygnal_gorne_pasmo_energii, self.transienty_gorne_pasmo, self.Q3_high)
        # self.transienty_gorne_pasmo


        # funkcja odpwoiedzilana za autokorelacje próbek transientów
        # dolne pasmo
        self.mozliwe_tempa = self.autokorelacja(self.transienty_dolne_pasmo)
        bpms_low = self.mozliwe_tempa.copy()
        # czyszczenie listy

        self.mozliwe_tempa = []
        self.mozliwe_tempa = self.autokorelacja(self.transienty_gorne_pasmo)
        bpms_high = self.mozliwe_tempa.copy()

        wszystkie_bpms = []

        # waga 3 dla low bo są wiele bardziej skuteczne niz high
        for i in bpms_low:
            wszystkie_bpms.append({"bpm": i["bpm"], "ilosc": i["ilosc"] * 3})

        # waga 1 dla high bo zazwyczaj dakją odchylone wyniki
        for i in bpms_high:
            wszystkie_bpms.append({"bpm": i["bpm"], "ilosc": i["ilosc"] * 1})

        # grupujemy podobne bpmy bo mogą się powtarzać z dokładnoscią do 1,3 BPM
        pogrupowane_bpms = []
        for i in range(0, len(wszystkie_bpms)):
            nowe_bpm = wszystkie_bpms[i]["bpm"]
            nowa_ilosc = wszystkie_bpms[i]["ilosc"]
            dodano = False

            for j in range(0, len(pogrupowane_bpms)):
                delta_bpm = abs(pogrupowane_bpms[j]["bpm"] - nowe_bpm)
                if delta_bpm <= 1.2:
                    pogrupowane_bpms[j]["ilosc"] = pogrupowane_bpms[j]["ilosc"] + nowa_ilosc
                    dodano = True
                    break
            if dodano == False:
                pogrupowane_bpms.append({"bpm": nowe_bpm, "ilosc": nowa_ilosc})

        self.info(f"Po pogrupowaniu mamy {len(pogrupowane_bpms)} unikalnych bpm")
        print(f"Po pogrupowaniu mamy {len(pogrupowane_bpms)} unikalnych bpm")

        # sortowanie
        pogrupowane_bpms.sort(key = lambda x: x["ilosc"], reverse = True)

        # Wyswietlanie w labelach
        pierwsze_3_mozliwe_bpm = pogrupowane_bpms[:3]
        for i in range(0, len(pierwsze_3_mozliwe_bpm)):
            bpm_wartosc = pierwsze_3_mozliwe_bpm[i]["bpm"]
            ilosc_wartosc = pierwsze_3_mozliwe_bpm[i]["ilosc"]
            tekst = f"{i + 1}. {bpm_wartosc} BPM ({ilosc_wartosc} razy powtórzeń)"

            if i == 0:
                self.label_bpm1.config(text=tekst)
                print(tekst)
            elif i == 1:
                self.label_bpm2.config(text=tekst)
                print(tekst)
            elif i == 2:
                self.label_bpm3.config(text=tekst)
                print(tekst)

        # Wykres
        bpms = []
        ilosci = []
        for i in range(0, len(pogrupowane_bpms)):
            bpms.append(pogrupowane_bpms[i]["bpm"])
            ilosci.append(pogrupowane_bpms[i]["ilosc"])

        plt.figure(figsize=(12, 8))
        plt.bar(bpms, ilosci, color="red")
        plt.title("Ranking BPM - z wagami")
        plt.xlabel("BPM")
        plt.ylabel("ilosc")
        plt.grid(True)
        plt.show()

    def autokorelacja(self, transienty):
        self.info("Start autokorelacji")
        print("Start autokorelacji")

        # Robię nową tabliće dla przechowywania tylko czasu w jakim był transient
        pozycje_transientow = []
        for i in range(0, len(transienty)):
            if transienty[i] == 1:
                pozycje_transientow.append(i)

        # mamy właśnie już całą liste nową wypełnioną pozycjami samych strasnwineów
        # sprawdźmy czy mamy wystarczająca ilosc do przeprowadzenia badania
        if len(pozycje_transientow) < 2:
            self.info("Mamy za malo transientow do przeprowadzenia badania")
            print("Mamy za malo transientow do przeprowadzenia badania")
            return # zatrzymujemy jeżeli mamy za malo transientow
        else:
            self.info(f"Znaleziono {len(pozycje_transientow)} transientow.")
            print(f"Znaleziono {len(pozycje_transientow)} transientow.")

        # =============================================================================
        # 2. ZNajdywanie bpm i dodawanie ich do tablicy
        self.info("Tworzymy listę ktora bedzie przechowwyac mozliwe bpm")
        print("Tworzymy listę ktora bedzie przechowwyac mozliwe bpm")
        lista_mozliwe_bpm = [] # lista która będzie przechowywac mozliwe bpm tylk z danego jednego pasma
        for i in range(0, len(pozycje_transientow) - 1):
            delta_probek = pozycje_transientow[i + 1] - pozycje_transientow[i]
            delta_probek_sek = delta_probek / self.sample_rate
            bpm = round(60/delta_probek_sek, 1) # to obliczy już nam bpm pierwszy

            if bpm >= 30 and bpm <= 170:
                lista_mozliwe_bpm.append(bpm)


        if len(lista_mozliwe_bpm) == 0:
            self.info("Nie znaleziono żadnego bpm w przedziale <30, 170>")
            print("Nie znaleziono żadnego bpm w przedziale <30, 170>")
            return

        # =============================================================================
        # 3. Grupowanie znalezionych bpm
        self.info("Grupujemy znalezione bpm")
        print("Grupujemy znalezione bpm")
        for i in range (0, len(lista_mozliwe_bpm)):
            nowe_bpm = lista_mozliwe_bpm[i]
            dodano = False

            for j in range(0, len(self.mozliwe_tempa)):
                delta_bpm = abs(self.mozliwe_tempa[j]["bpm"] - nowe_bpm)
                if delta_bpm <= 1:
                    self.mozliwe_tempa[j]["ilosc"] = self.mozliwe_tempa[j]["ilosc"] + 1
                    dodano = True
                    break

            if dodano == False:
                self.mozliwe_tempa.append({"bpm": nowe_bpm, "ilosc": 1})

        # =============================================================================
        # 3. Sortowanie

        self.mozliwe_tempa.sort(key=lambda x: x["ilosc"])
        self.mozliwe_tempa.reverse()

        pierwsze_3_mozliwe_bpm = self.mozliwe_tempa[:3]
        for i in range(0, len(pierwsze_3_mozliwe_bpm)):
            bpm_wartosc = pierwsze_3_mozliwe_bpm[i]["bpm"]
            ilosc_wartosc = pierwsze_3_mozliwe_bpm[i]["ilosc"]
            tekst = f"{i + 1}. {bpm_wartosc} BPM ({ilosc_wartosc} razy powtórzeń)"

            if i == 0:
                self.label_bpm1.config(text=tekst)
                print(tekst)
            elif i == 1:
                self.label_bpm2.config(text=tekst)
                print(tekst)
            elif i == 2:
                self.label_bpm3.config(text=tekst)
                print(tekst)

        # =============================================================================
        # 4. Sortowanie Wykresy
        bpms = []
        ilosci = []
        for i in range(len(self.mozliwe_tempa)):
            bpms.append(self.mozliwe_tempa[i]["bpm"])
            ilosci.append(self.mozliwe_tempa[i]["ilosc"])

        plt.figure(figsize = (12, 8))
        plt.bar(bpms, ilosci, color="red")
        plt.title("Ranking BPM - najbardziej mozliwych")
        plt.xlabel("BPM")
        plt.ylabel("ilosc")
        plt.grid(True)
        plt.show()

        return self.mozliwe_tempa


    def znajdz_transienty(self, sygnal_energii, transinty_tablica, Q3):
        for i in range (0, len(sygnal_energii)):
            if sygnal_energii[i] > Q3:
                transinty_tablica.append(1)
            else:
                transinty_tablica.append(0)

        self.info(f"Uzupełniono tablice transientów")

        plt.figure(figsize=(20, 10))
        plt.plot(transinty_tablica, color="#9933ff")
        plt.title("Wykres tablicy transientów")
        plt.xlabel("czas")
        plt.ylabel("Transienty")
        plt.grid(True)
        plt.show()
        self.info(f"Stworzono wykres dla tablicy transientów")



    def znajdz_Q3(self, sygnal_energii):
        if sygnal_energii == self.sygnal_dolne_pasmo_energii:
            copy_sygnal_energii = sygnal_energii.copy()
            copy_sygnal_energii.sort()
            self.info(f"posegregowana: {copy_sygnal_energii[:20]}")
            # ze wzoru na kwartl 3 z https://mfiles.pl/pl/index.php/Kwartyl#:~:text=Kwartyl%20Q1%20dzieli%20dane%20na,graficznie%20na%20podstawie%20krzywej%20ogiwalnej.
            Q3 = copy_sygnal_energii[int(len(copy_sygnal_energii) * 0.999 + 1)]
            self.info(f"Q3: {Q3}")
            self.info(f"Nowym Tresholdem zostanie: {Q3}")
            return Q3
        else:
            copy_sygnal_energii = sygnal_energii.copy()
            copy_sygnal_energii.sort()
            self.info(f"posegregowana: {copy_sygnal_energii[:20]}")
            # ze wzoru na kwartl 3 z https://mfiles.pl/pl/index.php/Kwartyl#:~:text=Kwartyl%20Q1%20dzieli%20dane%20na,graficznie%20na%20podstawie%20krzywej%20ogiwalnej.
            Q3 = copy_sygnal_energii[int(len(copy_sygnal_energii) * 0.9999 + 1)]
            self.info(f"Q3: {Q3}")
            self.info(f"Nowym Tresholdem zostanie: {Q3}")
            return Q3

    # https://stackoverflow.com/questions/12093594/how-to-implement-band-pass-butterworth-filter-with-scipy-signal-butter
    def oblicz_pasmo_energii(self, data, lowcut, highcut, fs, order):
        nyquist = fs / 2
        normalized_lowcut = lowcut / nyquist
        normalized_highcut = highcut / nyquist

        b, a = signal.butter(order, [normalized_lowcut, normalized_highcut], btype='band')
        y = signal.filtfilt(b, a, data)

        if lowcut == 20 and highcut == 80:
            for i in range(0, len(y) - 1):
                self.sygnal_dolne_pasmo_energii.append(abs(y[i+1] - y[i]))

            plt.figure(figsize=(20, 8))  # Duży rozmiar okna
            plt.plot(self.sygnal_dolne_pasmo_energii, color="#ff3399")
            plt.title(f"Energia dolnego pasma ({lowcut}-{highcut} Hz)")
            plt.xlabel("Czas")
            plt.ylabel("Energia")
            plt.grid(True)  # Siatka dla lepszej analizy
            plt.show()  # Tylko pokazuje, nie zapisuje
            self.info(f"Stworozny wykres znormalizowanej energii audio dla {lowcut}Hz - {highcut}Hz")
        else:
            for i in range(0, len(y) - 1):
                self.sygnal_gorne_pasmo_energii.append(abs(y[i+1] - y[i]))
            plt.figure(figsize=(20, 8))  # Duży rozmiar okna
            plt.plot(self.sygnal_gorne_pasmo_energii, color="#ff6633")
            plt.title(f"Energia dolnego pasma ({lowcut}-{highcut} Hz)")
            plt.xlabel("Czas")
            plt.ylabel("Energia")
            plt.grid(True)  # Siatka dla lepszej analizy
            plt.show()  # Tylko pokazuje, nie zapisuje
            self.info(f"Stworozny wykres znormalizowanej energii audio dla {lowcut}Hz - {highcut}Hz")

        self.info(f"Uzupełniono tablicę lowEnergii danymi. \n"
                  f"{y[::300000]}")





    def normalizacja_audio(self, audio_data=None):
        max_sample = max(abs(sample) for sample in audio_data)

        self.info(f"Max próbka audio to: {max_sample}")
        wspolczynnik_normalizacji = 30000 / max_sample

        self.normalized_audio_data = []
        for i in range(0, len(audio_data)):
            self.normalized_audio_data.append(audio_data[i] * wspolczynnik_normalizacji)

        return self.normalized_audio_data









if __name__ == '__main__':
    root = tk.Tk()
    apliakcja = EstymatorTempa(root)
    root.mainloop()


