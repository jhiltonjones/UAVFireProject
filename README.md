# MINDS6003 UAV Fire Program
This code was designed for the University of Southampton's module 'MINDS 6003', it is used to set a foundational idea of how the XPRIZE Wildfire challenge can be solved with a broader functionality of optimising fire suppression. This code has three sections: Clustering, Detection and the Practice Arena.
To run this code please ensure that ELMFIRE and SimFire has been properly installed with the environment correctly set up. Please refer to the proper documentation for each of fire modelling software (https://elmfire.io/) and (https://mitrefireline.github.io/simfire/).
When ELMFIRE and SimFire has been installed our code can be run from the terminal using:

```bash
python app.py
```
## Clustering
This is designed to run before the XPRIZE challenge and clusters the drones based on the speed of fire spread in every point of the map. To run this the user can click on the "Run Drone Clustering" button which they will be prompted to select the coordinates for the centre of the area they want to calculate a risk spread graph for and assign the suppressant drones.
The user will then be asked to put a buffer distance which is the distance from the center to the corners of the area. Lastly the weather will be required, including the wind speed, wind direction, moisture values over 1 hour, 10 hours, 100 hours, the live herbaceous moisture content and the live woody moisture content.
The program will cluster the area into 4 regions based on the spread rate of a potential fire at every point. It will also calculate the area of each of the quadrants, with the number of drones needed to complete the area. This is calculated using a sensor with a HFOV of 4200m and a speed of 22.73 m/s. 
The number of drones mapped is calculated depending on the size of the quadrant and risk of spread within 6 mins. Lastly the suppressant drones are assigned coordinates in the middle of each of the quadrants with one drone assigned the origin, therefore 5 suppressant drones in total.

## Detection and Within Challenge
Within the 10-minute challenge, the drones will detect, model and suppress the fire. The program can detect the fire using 3 layers of security using, a trained Random Forest model, a fine-tuned ResNet50 and using ELMFIRE. The hyperparameters were initialised using a grid-search for the Random Forest which achieved an accuracy of 84%. The ResNet50 was finetuned by unfreezing the weights and biases of the fully connected layer using a Kaggle dataset "FireVision". If a fire is predicted or the confidence is below 75% then the lower layer drone will predict the fire using the ResNet50, after this, the program will then model the fire. The fire is modelled using ELMFIRE which we can then produce stats and information from. ELMFIRE models the fire for the time it takes for the closest drone to arrive, which then produces maps of the operational roads, where the fire is on the map, with the optimal ellipse for the drone's travel route. If the fire needs a multi-agent which is calculated by the size of the fire and weight of the suppressant, the closest drone drops the suppressant on the fastest spreading direction (calculated by wind direction only), and then ELMFIRE models the fire once again for the furthest suppressant drone. The optimal route is calculated, with the amount of gallons of fire retardant used (Phos-Chek-LC95). The program flowchart can be seen below.

## Practice Arena


## Group Video
https://youtu.be/vrg9H3ZMUhQ
![alt text](https://github.com/jhiltonjones/UAVFireProject/blob/main/Flowchart_FireProgram.png?raw=true)
