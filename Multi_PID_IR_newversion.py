"""
Les Commentaires de cette forme indique un paramètre modifiable par l'utilisateur. TOUT LE RESTE DU CODE NE DOIT EN AUCUN CAS ÊTRE MODIFIE
Attention les texte de la forme "localhost" ligne 25 ne sont pas des commentaires mais des données
"""

# Un commentaire de cette forme indique une aide pour la compréhension du code

# Bibliothèques utilisées
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_rs232_v2 import BrickletRS232V2
from tinkerforge.bricklet_thermal_imaging import BrickletThermalImaging
from tinkerforge.brick_master import BrickMaster
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import PySimpleGUI as sg
import cv2
import keyboard
import pandas as pd
import datetime

# Initialisation des variables du module de la caméra
HOST = "localhost"
PORT = 4223
UID = "6eSrKP"
UID_RS = "W9P"
UID_CAMERA = "YYc"

"""
Variables de PID, uniquement les valeure en vert sont modifiable. Ne pas changer le nom des variables Kp,Ki et Kd.
Valeur par défaut : 50;1;10
"""
P = 1

Kp = 50
Ki = 1
Kd = 10

"""
rampe et température de maintien
"""
R = 60 # °C/min
M = 90 # °C

"""
Limitation puissance au démarrage
"""

Tlim = 4 #secondes
Pmax = 30 #alpha max

# initialisation des variables de gestions des points de lecture et d'acquisition de température

Point_read = []
Point_name = []
counter_read = 0

"""
Variables permettant d'associer des points d'acquisition de température à l'IR correspondant.
ATTENTION, le nombre x présent dans le range(x) doit correspondre au nombre d'IR présent dans la liste IR_name
les variables modifiables sont donc x et les noms des IR, ils est bien entendu possible d'ajouter/modifier/supprimer des noms, NE PAS OUBLIER LA VIRGULE.
La variable layout ligne 168 doit correspondre au nom présent dans IR_name, étudiez la mise en forme et faites correspondre les noms à IR_name.
"""
Associate_point = [[] for _ in range(12)] # 6 IR emitters
IR_associate = []
IR_name = [ "IR B1",
            "IR B2",
            "IR B3",
            "IR B4",
            "IR H5",
            "IR H6",
            "IR H7",
            "IR H8",
            "IR P9",
            "IR P10",
            "IR P11",
            "IR P12"
          ]

# Connexion du module
ipcon = IPConnection() # Create IP connection
rs232 = BrickletRS232V2(UID_RS, ipcon) # Create device object
ti = BrickletThermalImaging(UID_CAMERA, ipcon) # Create device object
master = BrickMaster(UID, ipcon) # Create device object
ipcon.connect(HOST,PORT)

"""
Valeur d'émissivité comprise entre 0 et 100, entier
défaut : 95
"""

emissivity = 90 

#Emissivity setting
e_coeff = int(emissivity*2048/25)
ti.set_flux_linear_parameters(scene_emissivity = e_coeff, temperature_background = 29515, tau_window = 8192, temperatur_window = 29515, tau_atmosphere = 8192, temperature_atmosphere = 29515, reflection_window = 0, temperature_reflection = 29515)


def temperature_image(image):                   # function that convert the thermal image in uint8 60*80 pixels with each pixels equals to °C between 0 & 255
    # image is an tuple of size 80*60 with a 16 bit grey value for each element
    reshaped_image = np.array(image, dtype=np.float16).reshape(60, 80)
    color = np.array(image, dtype=np.uint8).reshape(60, 80)
    frame = cv2.applyColorMap(color,cv2.COLORMAP_PLASMA)
    frame = cv2.resize(frame, (600, 800), interpolation=cv2.INTER_CUBIC)
    reshaped_image = (reshaped_image/100-273.15)

    for i in range(0,len(Point_read),2):
                            # for loop for Point_read drawing
        cv2.putText(frame, IR_name[Associate_point[i]]+" : "+str(reshaped_image[int((6/8)*Point_read[i+1]/10)][int((8/6)*Point_read[i]/10)]),(Point_read[i], Point_read[i+1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36,255,12), 2)
        cv2.circle(frame, (Point_read[i], Point_read[i+1]), 3, (0, 255, 0), 2)        

    cv2.imshow("frame",frame)
    cv2.waitKey(1)
    return(reshaped_image)


def Win_name():

    global Point_name

    layout = [
              [sg.Text("Entrez nom point")],
              [sg.In()],
              [sg.Button("Valider")]
             ]

    name = sg.Window("IR set",layout)

    while True :

        event, values = name.read(timeout = 10)

        if event == 'Valider':
            Point_name[-1] = layout[0][1].get()
            name.close()
            break

        if event == sg.WIN_CLOSED:
            Win_name()
            break


def mousePoints(event,x,y,flags,params):            # Mouse event fonction

    global Point_read
    global counter_read
    global Point_name
    global IR_associate

    # Left button mouse click event -> Store x and y in Point_reg and then increase by 2 counter_reg
    if event == cv2.EVENT_LBUTTONDOWN :    

        Point_read.append(x)
        Point_read.append(y)
        counter_read += 1
        Point_name.append(counter_read)
        IR_associate = [' ' for _ in range(counter_read)]
        Win_name()

    # Right button mouse click event -> clear window of different points        
    elif event == cv2.EVENT_RBUTTONDOWN:
        counter_read = 0
        Point_read = []


def cb_high_contrast_image():                    # Getter function for image acquisition, return uint8 640*480 array of high contrast image, see https://www.tinkerforge.com/en/doc/Software/Bricklets/ThermalImaging_Bricklet_Python.html#BrickletThermalImaging.set_image_transfer_config for more details
    
    global frame

    image = ti.get_high_contrast_image()
    
    # image is an tuple of size 80*60 with a 8 bit grey value for each element
    frame = np.array(image, dtype=np.uint8).reshape(60, 80)
    # scale image 8x
    frame = cv2.applyColorMap(frame,cv2.COLORMAP_PLASMA)
    frame = cv2.resize(frame, (600, 800), interpolation=cv2.INTER_CUBIC)
    
    for i in range(0,len(Point_read),2):
        if i+1 <= len(Point_read):
                                # for loop for boxes drawing
            try : cv2.putText(frame,Point_name[i]+' '+str(IR_associate[int(i/2)]),(Point_read[i], Point_read[i+1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36,255,12), 2)
            except : None
            cv2.circle(frame, (Point_read[i], Point_read[i+1]), 3, (0, 255, 0), 2)

    cv2.imshow("elements",frame)
    cv2.waitKey(1)
    cv2.setMouseCallback("elements", mousePoints)


def Win_attribuer():

    global Associate_point
    global IR_associate

    layout = [[sg.Text(str(i)), sg.Combo(IR_name+[''],readonly=True)] for i in range(counter_read)]+[
              [sg.Text("Un IR doit être associé à un unique point de régulation et réciproquement"),
               sg.Button("Valider")]
             ]
   
    attribution = sg.Window("IR attribution",layout)

    while True :

        event, values = attribution.read(timeout = 10)

        if event == "Valider":

            Associate_point = [[] for _ in range(12)] # 6 IR emitters
            for i in range(len(IR_name)):

                for j in range(len(layout)-2):
                
                    IR_associate[j] = layout[j][1].get()

                    if layout[j][1].get() == IR_name[i]:
                        Associate_point[i].append(j)

            attribution.close()
            Win_element()
            break

        if event == sg.WIN_CLOSED:
            Win_attribuer()
            break


def Win_element():
    layout = [
              [sg.Button("Valider")],
              [sg.Button("Attribuer IR")]
             ]

    elements = sg.Window("IR set",layout)

    ti.set_image_transfer_config(ti.IMAGE_TRANSFER_MANUAL_HIGH_CONTRAST_IMAGE)

    while True:

        event, values = elements.read(timeout=10)

        cb_high_contrast_image()

        if keyboard.is_pressed('enter'):
            break
            
        if event == 'Valider':
            break

        if event == sg.WIN_CLOSED:
            ipcon.disconnect()
            return None
        
        if event == "Attribuer IR":
            elements.close()
            Win_attribuer()

    ti.set_image_transfer_config(ti.IMAGE_TRANSFER_MANUAL_TEMPERATURE_IMAGE)
    ti.set_resolution(1)
    elements.close()
    cv2.destroyAllWindows()


def write_excel():                                  # data save to excel using Pandas
    now = datetime.datetime.now()
    dt_string = now.hour+'_'+now.minute+'_'+now.second
    writer = pd.ExcelWriter('Excel regulation'+dt_string+'.xlsx')      # change name between executions if you don't want to overwrite
    vehicule_pd = pd.DataFrame([T,Consigne]+Temperature)
    vehicule_pd.to_excel(writer,sheet_name="Temps, consigne, Température",index=False, header=False)  # No index & header needed, this files isn't make for human reading
    writer.save()

Win_element()

t0 = time.time()

t = 0

alpha = [[0] for _ in range(len(IR_name))]
error = [0 for _ in range(len(IR_name))]
p_error = [0 for _ in range(len(IR_name))]
integral = [0 for _ in range(len(IR_name))]

ti.set_image_transfer_config(ti.IMAGE_TRANSFER_MANUAL_TEMPERATURE_IMAGE)
ti.set_resolution(1)
bin = temperature_image(ti.get_temperature_image())[30][40]

T = [0]

T0 = temperature_image(ti.get_temperature_image())[30][40]

Temperature = [[T0] for _ in range(counter_read)]

Consigne = [T0]

layout = [
        [sg.Canvas(key="-CANVAS-",expand_x = True,expand_y = True)],
        [sg.Button("Fin de l'acquisition et calcul des alphas")]       
        ]
    
window = sg.Window("Graphe",layout,finalize=True)

canvas_elem = window['-CANVAS-']
canvas = canvas_elem.TKCanvas

def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

fig = Figure()
ax = fig.add_subplot(111)
ax.set_ylabel("temperature axis (°C)")
ax.set_xlabel("Time axis (s)")
ax.grid()
fig_agg = draw_figure(canvas, fig)

Alpha_montee = [0 for _ in range(IR_name)]
Alpha_maintien = [0 for _ in range(IR_name)]
temps_montee = (M-T0)/(R/60)

while True :

    event,values = window.read(timeout = 10)

    if event == "Fin de l'acquisition et calcul des alphas":
        rs232.write([chr(0) for _ in range(len(IR_name))])
        window.close()
        break

    if keyboard.is_pressed('ctrl+space'):
        break

    message = [chr(0) for _ in range(len(IR_name))]
    message[-1] = 2

    tp = t
    t= time.time()-t0

    dt = t - tp

    T.append(t)

    if ti.get_statistics()[3] == 2:
        continue

    temperature = temperature_image(ti.get_temperature_image())

    consigne = T0 + t*R/60

    if consigne > M:
        consigne = M
   
    Consigne.append(consigne)

    ax.cla()
    ax.grid()

    ax.plot(T,Consigne,label= "Consigne")

    for i in range(0,int(len(Point_read)/2)):

        k = Associate_point[i]

        if not k:
            message[k] = 0
            continue
        
        temp = 0
        for t in k :
            temp += temperature[int((6/8)*Point_read[2*t+1]/10)][int((8/6)*Point_read[2*t]/10)]
        Temperature[i].append(temp/len(k))

        error[i] = consigne - Temperature[i][-1]
        integral[i] += error[i] * dt
        derivative = (error[i] - p_error[i])/dt

        alpha[i].append(int(alpha[i][-1] + P*(Kp*error[i] + Ki*integral[i] + Kd*derivative)))

        p_error[i] = error[i]

        if alpha[i][-1] < 0:
            alpha[i][-1] = 0
    
        if alpha[i][-1] > 100:
            alpha[i][-1] = 100

        if alpha[i][-1] > Pmax and t < Tlim :
            alpha[i][-1] = Pmax

        ax.plot(T,Temperature[i],label=IR_name[i]+" : "+str(Temperature[i][-1]))
        message[k] = chr(alpha[i][-1])
    
    for i in range(int(len(Point_read)/2)):
    
        Temperature[i].append(temperature[int((6/8)*Point_read[2*i+1]/10)][int((8/6)*Point_read[2*i]/10)])

        ax.plot(T,Temperature[i],label="Lecture "+str(i+1)+" : "+str(Temperature[i][-1]))
    
    ax.legend()
    fig_agg.draw()

    rs232.write(message)

message = [chr(0) for _ in range(len(IR_name))]
message[-1] = chr(2)

rs232.write(message)

write_excel()

i=0 
t = T[i]

while t<temps_montee:

    for j in range(len(IR_name)):
        Alpha_montee[j] += (alpha[j][i]*(T[i+1]-T[i]))
    
    t=T[i]
    i+=1

Alpha_montee /= temps_montee

for j in range(i,len(T)-1): 

    for k in range(len(IR_name)):
        Alpha_maintien[k] += alpha[k][j]*(T[j+1]-T[j])
    j+=1

Alpha_maintien /= (T[-1]-temps_montee)

print(" Alphas rampe : ")
for i in range(len(IR_name)):
    print(" Alpha rampe " + IR_name[i] + " = " + str(Alpha_montee[i]))

print(" Alphas maintien : ")
for i in range(len(IR_name)):
    print(" Alpha maintien " + IR_name[i] + " = " + str(Alpha_maintien[i]))

ipcon.disconnect()