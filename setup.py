from setuptools import find_packages, setup

setup(
    name="src",
    packages=find_packages(),
    version="0.1.0",
    description="Artificial intelligence–based quantification of breast arterial calcifications to predict cardiovascular morbidity and mortality",
    author="Renan Costa Alencar",
    license="MIT",
    install_requires=[
        "numpy>=1.24.0",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "pydicom>=2.4.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "albumentations>=1.3.0",
        "boto3>=1.28.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "scikit-learn>=1.3.0",
        "tensorboard>=2.14.0",
    ],
    python_requires=">=3.8",
)
