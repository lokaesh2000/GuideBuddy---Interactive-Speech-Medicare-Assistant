# GuideBuddy: Interactive Speech Medicare Assistant

## 🏥 Project Overview

GuideBuddy is an advanced AI-powered medical assistance platform designed to revolutionize healthcare communication through intelligent, speech-enabled interactions.

![GuideBuddy Logo](logo_placeholder.png)

### 🌟 Key Features
- 🎙️ Speech-to-Text & Text-to-Speech Capabilities
- 🤖 AI-Powered Medical Conversations
- 📄 Medical Document Analysis
- 👩‍⚕️ Specialist Consultation Simulator
- 🔒 Secure User Authentication
- 💬 Comprehensive Messaging System

## 🚀 Technology Stack

### Languages
- Python 3.8+

### Key Technologies
- **Frontend**: Tkinter
- **AI Integration**: 
  - Google Gemini AI
  - Whisper (Speech Recognition)
  - Eleven Labs (Text-to-Speech)
- **Backend**: 
  - Multi-agent AI System
  - Secure File Management

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Clone the Repository
```bash
git clone https://github.com/your-username/guidebuddy.git
cd guidebuddy
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure API Keys
1. Create `config/api_keys.json`
2. Add your API keys:
```json
{
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "elevenlabs_api_key": "YOUR_ELEVENLABS_API_KEY"
}
```

## 🖥️ Running the Application
```bash
python main.py
```

## 📋 User Types
- Patients
- Healthcare Professionals

## 🔐 Authentication
- Secure user registration
- Role-based access (Patient/Doctor)
- Password hashing

## 🌈 Key Modules

### 1. Authentication Module
- User registration
- Secure login
- Profile management

### 2. Chat Interface
- AI Medical Assistant
- Specialist Consultation
- Speech Input/Output

### 3. Document Management
- Medical document upload
- Document analysis
- Report generation

### 4. Messaging System
- Secure communication
- File sharing
- Conversation history

## 🚧 Current Limitations
- Version 1.0 Prototype
- Limited medical knowledge base
- Requires internet connection
- Dependency on external AI services

## 🔜 Upcoming Features
- Enhanced AI models
- Multilingual support
- Advanced predictive health insights
- Integration with health tracking devices

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 License
[Specify your license - e.g., MIT License]

## 📞 Contact
- Project Lead: [Your Name]
- Email: [Your Email]
- Project Link: [Repository URL]

## 🙏 Acknowledgments
- Google Gemini AI
- Whisper Speech Recognition
- Eleven Labs
- Open-source community

## 📊 Version
- Current: 1.0 (Prototype)
- Status: Active Development

## 💡 Vision
Democratizing medical information and improving healthcare communication through innovative AI technology.

---

GuideBuddy Architecture: A Comprehensive System Design
🏗️ Architectural Overview
GuideBuddy is designed with a sophisticated, modular architecture that ensures scalability, flexibility, and robust medical information processing. The system is strategically organized into multiple layers, each with distinct responsibilities and interactions.
1. Presentation Layer (Views)
Purpose
The presentation layer is the user's primary interaction point, responsible for rendering interfaces and capturing user inputs across different user types.
Key Components

Authentication View

Manages user login and registration
Handles user type differentiation (Patient/Doctor)
Implements secure access control


Patient View

Provides a comprehensive medical assistant interface
Includes specialized panels for:

AI Medical Assistant Chat
Specialist Consultation
Document Management
File Sharing
Messaging System




Doctor View

Offers advanced medical management capabilities
Panels include:

Patient Management
Document Analysis
Medical Reference
Communication Channels





2. Controller Layer
Purpose
Acts as the application's brain, coordinating communication between views and underlying services, implementing core business logic.
Key Controllers

Authentication Controller

User credential validation
Session management
Role-based access control
Secure user registration process


Chat Controller

Manages conversational workflows
Handles message processing
Maintains conversation context
Interfaces with AI language models
Manages conversation history and summaries


Document Controller

Manages document upload processes
Coordinates document analysis
Generates medical reports
Handles file storage and retrieval


Message Controller

Manages user-to-user communication
Handles message routing
Implements secure messaging protocols



3. Service Layer
Purpose
Provides core application services, interfaces with external APIs, and processes complex operations.
Key Services

Language Model (LLM) Service

Integrates with Gemini AI
Processes natural language queries
Generates intelligent, context-aware responses
Manages multi-turn conversations
Implements prompt engineering techniques


Speech Service

Speech-to-Text conversion
Text-to-Speech generation
Audio processing and quality enhancement
Supports multiple audio input/output scenarios


Message Service

Manages user messaging ecosystem
Stores and retrieves conversations
Implements secure communication channels
Supports file attachments
Maintains message history



4. Agent Layer
Purpose
Provides specialized processing for different document types and domain-specific analysis.
Specialized Agents

Text Agent

Processes text-based medical documents
Extracts key medical information
Analyzes medical reports and narratives


Image Agent

Analyzes medical images
Processes scans, X-rays, and medical photographs
Extracts and interprets visual medical data


Structured Agent

Processes structured medical data
Analyzes spreadsheets, CSV files
Handles lab reports and numerical medical records


Specialist Agent

Simulates domain-specific medical consultations
Provides specialized medical guidance
Adapts communication based on medical specialty



5. Data Layer
Purpose
Manages data storage, retrieval, and persistence across the application.
Key Data Management Features

Secure user data storage
Encrypted medical document management
Conversation history preservation
User profile management
Compliance with medical data protection standards

6. Security Architecture

Multi-layered authentication
Role-based access control
End-to-end encryption
Secure API communications
Compliance with medical data privacy regulations

7. Technological Integration

Frontend: Tkinter for cross-platform UI
Backend: Python with modular, event-driven architecture
AI Integration:

Google Gemini for conversational AI
Whisper for speech recognition
Eleven Labs for text-to-speech



8. Scalability and Extensibility

Microservices-inspired modular design
Loosely coupled components
Easy integration of new medical specialties
Adaptable to future AI and technology advancements

Architectural Principles

Modularity: Each component has a specific, well-defined responsibility
Separation of Concerns: Clear boundaries between different system layers
Flexibility: Easy to modify and extend individual components
Performance: Efficient processing and minimal latency
Security: Robust protection of sensitive medical information

Future Evolution
Version 1.0 lays the groundwork for a comprehensive, AI-powered medical assistant. Future iterations will focus on:

Advanced AI model refinement
Expanded medical knowledge bases
Enhanced personalization
Deeper integration with healthcare ecosystems

**Disclaimer**: GuideBuddy is an AI assistant and does not replace professional medical advice. Always consult healthcare professionals for medical decisions.
