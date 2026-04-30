# **Project Title:** Object-Detection-with-LLM-pipeline-triggering-ICT740-Group03

**Edge AI Microservice for Object Detection and LLM Analysis using the Google Coral Dev Board**

## Subject

**ICT740: Hardware Designs for Artificial Intelligence & Internet of Things, 2026**  
**Group 03**

---

## Quick Note

To set up the **Google Coral Dev Board integration with the camera detection logic**, please follow this repository:

[https://github.com/PPipat2002/Dev-board-Coral](https://github.com/PPipat2002/Dev-board-Coral)

For more detailed explanation, system design, implementation process, and demonstration, we also provide a Medium blog:

[https://medium.com/@brnto97/edge-to-cloud-ai-pipeline-with-google-coral-dev-board-smart-book-detection-237f84774a5c](https://medium.com/@brnto97/edge-to-cloud-ai-pipeline-with-google-coral-dev-board-smart-book-detection-237f84774a5c)

---

## **Member**

| No. | Name | ID | Email |
|---|---|---|---|
| 1. | Nawaphol Worakijthamrongchai (Ben) | 6822040314 | nawa.2003.worakij@gmail.com |
| 2. | Pornpipat Varin | 6822040421 | ppipat.varin@gmail.com |
| 3. | Ploypilin Prutpinit | 6814552833 | ploy8608@gmail.com |

---

## **Overview**

This project implements a **Vision-to-LLM Trigger Pipeline** using the **Google Coral Dev Board**, **Edge TPU**, **FastAPI**, **Gemini API**, **MongoDB Atlas**, and a **Next.js dashboard**.

The main idea is to use the Coral Dev Board as an **edge AI trigger device**. The board continuously performs real-time object detection from a USB camera. When the target object, in this case a **book**, is detected with sufficient confidence, the system captures a still image and sends it to the backend server through the local network.

The backend server stores the captured image, records detection metadata into MongoDB Atlas, sends the image to the Gemini API for visual analysis, and stores the LLM-generated result in a separate collection. The final result is then displayed on a web dashboard.

This project demonstrates how **Edge AI** and **Cloud LLMs** can work together efficiently. Instead of sending every video frame to the cloud, the edge device filters the input locally and only triggers cloud processing when meaningful events occur.

---

## **Objective**

The main objective of this project is to demonstrate the integration of hardware implementation with Artificial Intelligence and Internet of Things (AIoT) applications.

The specific objectives are:

1. To successfully flash, configure, and deploy the Google Coral Dev Board as an edge AI microservice.
2. To run a TensorFlow Lite object detection model on the Edge TPU for real-time object detection.
3. To build an event-driven pipeline that captures an image only when the target object is detected.
4. To send the captured image to a backend server through the local network.
5. To store detection logs and LLM analysis results using MongoDB Atlas.
6. To use the Gemini API for visual analysis and structured text generation.
7. To develop a Next.js dashboard that displays captured images, detection logs, and LLM-generated analysis.

---
## **System Architecture**
<img width="1400" height="800" alt="SystemDiagramHardware drawio" src="https://github.com/user-attachments/assets/92a0747d-0502-4aaf-b3b5-bc52500c0db5" />

---
## **Flowchart**
<img width="2048" height="5649" alt="FlowChart1" src="https://github.com/user-attachments/assets/5068d9ab-590b-42b8-91f8-bfaf5d243904" />

<img width="1239" height="8192" alt="FlowChart2" src="https://github.com/user-attachments/assets/5c6760e5-ece8-4ef3-8e3f-43cc455048e6" />

---
## **Materials**

### Hardware

| Hardware | Purpose |
|---|---|
| Google Coral Dev Board | Main edge AI device used to run real-time object detection with Edge TPU acceleration. |
| U58 1080P HD USB Camera | Captures the live video stream and provides input frames for object detection. |
| MicroSD Card | Used to flash Mendel Linux into the Coral Dev Board internal storage. |
| USB-C Power Supply | Provides power to the Coral Dev Board. |
| USB-C Data Cable | Used to connect the host computer to the Coral Dev Board for MDT access. |
| Host Computer / Laptop | Used for development, backend hosting, and dashboard testing. |
| Wi-Fi / Local Network | Allows the Coral Dev Board to send captured images to the backend server. |

### Software

| Software / Framework | Usage |
|---|---|
| Mendel Linux | Operating system used on the Google Coral Dev Board. |
| TensorFlow Lite | Runs the object detection model on the Edge TPU. |
| Edge TPU Runtime | Enables hardware acceleration on the Coral Dev Board. |
| Python | Main programming language for the edge and backend logic. |
| OpenCV | Used for camera frame handling and image processing. |
| FastAPI | Backend framework for receiving images and handling API logic. |
| Uvicorn | ASGI server used to run the FastAPI backend. |
| MongoDB Atlas | Cloud database used to store detection logs and LLM analysis results. |
| Gemini API | Used for visual analysis and structured text generation. |
| Next.js / React | Used to build the frontend dashboard. |
| TypeScript | Used in the frontend for structured development. |
| Tailwind CSS | Used for dashboard styling. |

---

# **Backend Setup**

Move into the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Activate the environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add the required environment variables:

```env
MONGO_URI=your_mongodb_atlas_connection_string
GEMINI_API_KEY=your_gemini_api_key
```

Run the backend server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The `--host 0.0.0.0` option allows the backend server to receive requests from other devices on the same local network, including the Coral Dev Board.

---

# **Frontend Setup**

Move into the frontend folder:

```bash
cd book-detection-ui
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Open the dashboard in the browser:

```text
http://localhost:3000
```

---

## **Coral Dev Board Setup**

The Coral Dev Board is responsible for real-time object detection and image capture.

Please follow the Coral setup repository for:

- Flashing Mendel Linux
- Accessing the board with MDT
- Connecting to Wi-Fi
- Checking the USB camera
- Running the object detection script
- Sending captured images to the backend server

Example command to run the detection client:

```bash
python3 detect_client.py --server_url http://<BACKEND_SERVER_IP>:8000
```

Replace `<BACKEND_SERVER_IP>` with the IP address of the computer running the FastAPI backend.

Coral setup repository:

[https://github.com/PPipat2002/Dev-board-Coral](https://github.com/PPipat2002/Dev-board-Coral)

---

## **Demonstration**

For full demonstration, please visit this YouTube link:

[https://www.youtube.com/watch?v=HoLkAScV__A&feature=youtu.be](https://www.youtube.com/watch?v=HoLkAScV__A&feature=youtu.be)

---

## **Conclusion**

This project demonstrates a practical Edge-to-Cloud AI pipeline by combining hardware-level object detection with cloud-based LLM analysis. The Google Coral Dev Board performs fast local inference using the Edge TPU, while the backend server and Gemini API handle higher-level visual reasoning and structured text generation.

The system shows how edge hardware can act as a smart trigger for cloud AI services, reducing unnecessary API calls and network usage while still enabling intelligent analysis through a web dashboard.

This project highlights key skills in:

- Edge AI deployment
- AIoT system integration
- Real-time object detection
- FastAPI backend development
- MongoDB Atlas database integration
- Gemini API integration
- Next.js dashboard development

---

## **References**

- Google Coral Dev Board Documentation:  
  [https://coral.ai/docs/dev-board/get-started/](https://coral.ai/docs/dev-board/get-started/)

- TensorFlow Lite Documentation:  
  [https://www.tensorflow.org/lite](https://www.tensorflow.org/lite)

- FastAPI Documentation:  
  [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)

- Gemini API Documentation:  
  [https://ai.google.dev/](https://ai.google.dev/)

- MongoDB Atlas Documentation:  
  [https://www.mongodb.com/docs/atlas/](https://www.mongodb.com/docs/atlas/)

- Next.js Documentation:  
  [https://nextjs.org/docs](https://nextjs.org/docs)
