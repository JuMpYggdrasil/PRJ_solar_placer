import cv2

# Path to the image you want to enhance
image_path = 'C:\\Users\\Egat\\Documents\\GitHub\\PRJ_solar_placer\\asdf.jpg'

# Load the image
image = cv2.imread(image_path)

# Check if the image is loaded correctly
if image is None:
    raise ValueError(f"Image at path {image_path} could not be loaded. Please check the path.")

# Load the pre-trained super-resolution model
sr = cv2.dnn_superres.DnnSuperResImpl_create()

# Path to the EDSR_x4 model file (update this path to where you saved the model)
model_path = 'EDSR_x4.pb'
sr.readModel(model_path)
sr.setModel("edsr", 4)  # "edsr" is the model name, 4 is the upscaling factor

# Check the dimensions of the image
print(f"Original image dimensions: {image.shape}")

# Upscale the image
try:
    result = sr.upsample(image)
except cv2.error as e:
    print(f"Error during upsampling: {e}")
    raise

# Path to save the enhanced image
output_path = 'path_to_save_enhanced_image.jpg'
cv2.imwrite(output_path, result)

# Display the images (optional)
cv2.imshow('Original Image', image)
cv2.imshow('Enhanced Image', result)
cv2.waitKey(0)
cv2.destroyAllWindows()
