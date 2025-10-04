# Orbital Viewer Project

This project is a full-stack application for visualizing orbital trajectories in 3D. It consists of a **backend** built with FastAPI and a **frontend** built with React and Three.js.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up WSL with Docker](#setting-up-wsl-with-docker)
- [Forking and Cloning via HTTPS](#forking-and-cloning-via-https)
- [Running the Project](#running-the-project)

---

## Prerequisites

Before proceeding, ensure you have the following installed on your system:

- **Windows Subsystem for Linux (WSL)**: Install a WSL 2-compatible Linux distribution (e.g., Ubuntu).
- **Docker CLI**: Ensure Docker is installed and configured to work with WSL 2.
- **Git**: If not included with WSL distro Install Git for version control.

---

## Setting Up WSL with Docker

1. **Install WSL**:
   Open PowerShell as Administrator and run:

   ```powershell
   wsl --install
   ```

   Restart your system if prompted.

2. **Install a Linux Distro**:
   After restarting, open a terminal and set up your preferred Linux distribution (e.g., Ubuntu).

3. **Install Docker in WSL**:
   Inside your WSL terminal, run the following commands:

   ```bash
   sudo apt update
   sudo apt install -y docker.io
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

4. **Enable Docker with Systemd**:
   Edit the WSL configuration file to enable systemd:

   ```bash
   sudo nano /etc/wsl.conf
   ```

   Add the following lines:

   ```
   [boot]
   systemd=true
   ```

   Save and exit the file. Restart WSL:

   ```powershell
   wsl --shutdown
   wsl
   ```

5. **Verify Docker Installation**:
   Run the following command to verify Docker is running:
   ```bash
   sudo docker run hello-world
   ```

---

## Forking and Cloning via HTTPS

1. **Fork the Repository**:
   - Visit the original repository in your browser (e.g., `https://github.com/ORIGINAL_OWNER/orbital_viewer`).
   - Click **Fork** (top-right) and create your copy under your GitHub account.

2. **Clone Your Fork (HTTPS)**:
   In your WSL terminal:
   ```bash
   git clone https://github.com/<your-username>/orbital_viewer.git
   cd orbital_viewer
   ```

3. **Add Upstream Remote (optional but recommended)**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/orbital_viewer.git
   git fetch upstream
   ```

4. **Keep Your Fork Updated**:
   ```bash
   git checkout develop   # or main depending on default branch
   git pull upstream develop
   git push origin develop
   ```

5. **Create a Feature Branch** (workflow suggestion):
   ```bash
   git checkout -b feature/some-improvement
   # ...make changes...
   git add .
   git commit -m "feat: describe your change"
   git push -u origin feature/some-improvement
   ```

6. **Open a Pull Request**:
   - Go to your fork on GitHub, you’ll see a banner suggesting a PR.
   - Compare against the upstream `develop` (or `main`) branch.
   - Fill in a clear description and submit.

---

## Running the Project

1. **Open the Dev Container**:
   Open the project in Visual Studio Code. When prompted, reopen the project in the Dev Container.

2. **Install Dependencies**:
   The Dev Container will automatically install dependencies for both the backend and frontend.

3. **Start the Backend**:
   From the project root (recommended) run:
   ```bash
   uvicorn backend.app:app --reload
   ```

4. **Start the Frontend (development)**:
   ```bash
   cd frontend
   npm install   # first time only
   npm run dev   # serves on http://localhost:5173
   ```
   In dev mode the frontend calls the backend at http://localhost:8000 (adjust env vars if needed).

5. **Serve Built Frontend via Backend**:
   From `frontend/`:
   ```bash
   npm run build
   ```
   Then restart the backend server. The built assets under `frontend/dist` will be served at:
   http://localhost:8000

6. **Access the Application**:
   - Dev Frontend: http://localhost:5173
   - Backend API docs: http://localhost:8000/docs
   - Integrated (after build): http://localhost:8000

---

## Notes

- Ensure Docker is running and integrated with WSL.
- If you encounter issues, check the logs in the terminal or Dev Container output.

Happy coding!
