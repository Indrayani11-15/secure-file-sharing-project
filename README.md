# Secure Cloud File Sharing using Watermarking and Encryption

A secure cloud-based platform that enables safe file sharing using advanced cryptographic techniques and digital watermarking to protect data confidentiality and ownership.

## Live Project
Access the deployed application here:

[https://secure-file-sharing-p.onrender.com/](https://secure-file-sharing-p.onrender.com/)

---

## Project Description

Traditional cloud storage platforms provide convenience but often lack strong security mechanisms to ensure confidentiality and ownership verification. This project introduces a secure file sharing platform that integrates encryption and watermarking techniques to protect sensitive data.

The system encrypts uploaded files before storage and embeds hidden ownership information using digital watermarking techniques. Only authorized users can request access to files, and the owner can approve or reject these requests. Secure key distribution is handled through authenticated email communication.

This architecture ensures that data remains protected even in cloud environments, while also providing proof of ownership and controlled sharing capabilities.

---

## Key Features

• Secure file encryption before storage  
• Digital watermarking for ownership verification  
• Role-based authentication system  
• Secure key distribution via email  
• Controlled file sharing between owners and users  
• Multi-user system with server, owner, and user roles  

---

## System Roles

### Server / Admin
Approves registered users and owners and manages the system.

### File Owner
Uploads files, encrypts them, embeds watermark signatures, and approves access requests.

### User
Searches available files, requests access from the owner, and downloads files securely after approval.

---

## Technologies Used

Backend  
Python  
Flask Framework  

Database  
SQLite  

Security Libraries  
ECIES (Elliptic Curve Encryption)  
Fernet Encryption  
SHA-256 Hashing  
LSB Steganography for watermarking  

Communication  
SMTP Email Protocol  

Deployment  
Render Cloud Platform  
GitHub  

---

## System Workflow

1. Owner uploads file to the platform  
2. File is encrypted using cryptographic algorithms  
3. Ownership information is embedded using watermarking  
4. Encrypted file is stored securely on the server  
5. User searches and requests access to the file  
6. Owner approves the request  
7. Access keys are sent securely via email  
8. Authorized user decrypts and downloads the file  

---

## Running the Project Locally

Clone the repository

git clone https://github.com/indrayani11-15/secure-file-sharing-project.git

Navigate to the project directory

cd secure-file-sharing-project

Install dependencies

pip install -r requirements.txt

Run the application

python App_v2.py

Open the application in browser



---

## Author

Indrayani Verulkar  
B.Tech Computer Science Engineering

---

## License

This project is developed for academic and research purposes.
