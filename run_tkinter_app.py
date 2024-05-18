import tkinter as tk
import random
from PIL import Image, ImageTk
from torchvision.models import resnet50
from torchvision.datasets import ImageFolder
from torchvision import transforms
import torch

prediction_file = "prediction_result.txt"

model_file = './models/resnetmodel/resnet_model_default.pth'
model = resnet50(weights=None)
model.fc = torch.nn.Linear(2048, 2)
model.load_state_dict(torch.load(model_file))
model.eval()

image_size = (224, 224)
transform = transforms.Compose([
    transforms.Resize(image_size),
    transforms.ToTensor()
])

test_dataset = ImageFolder("./configs/data/archive/Classification/test", transform)
test_dataset2 = ImageFolder("./configs/data/archive/Classification/train", transform)
test_images = test_dataset.imgs + test_dataset2.imgs

def select_random_image():
    img_path, _ = random.choice(test_images)
    return img_path

def load_image(img_path):
    image = Image.open(img_path)
    image = transform(image).unsqueeze(0)
    return image

def predict_image(image_tensor):
    with torch.no_grad():
        output = model(image_tensor)
        _, predicted = torch.max(output, 1)
    return predicted.item()

def display_image():
    img_path = select_random_image()
    img = Image.open(img_path)
    img = img.resize((224, 224), Image.LANCZOS)
    img = ImageTk.PhotoImage(img)
    
    image_label.config(image=img)
    image_label.image = img
    
    image_tensor = load_image(img_path)
    class_idx = predict_image(image_tensor)
    class_name = test_dataset.classes[class_idx]
    
    prediction_label.config(text=f"Prediction: {class_name}")

    with open(prediction_file, 'w') as file:
        file.write(class_name)

    with open('prediction_done.txt', 'w') as f:
        f.write('done')

def main():
    global image_label, prediction_label

    root = tk.Tk()
    root.title("Image Classification")

    image_label = tk.Label(root)
    image_label.pack()

    prediction_label = tk.Label(root, text="Prediction: ", font=("Helvetica", 16))
    prediction_label.pack()

    button = tk.Button(root, text="Load UAV Data", command=display_image)
    button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
