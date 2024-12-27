<div align="center">
    <img src="https://github.com/user-attachments/assets/e9680077-f045-4afd-9375-989dacc52152" alt="" height="200">
</div>

<p align="center">
  <a href="https://discord.gg/tloxp">
    <img src="https://ptb.discord.com/api/guilds/1258060134060654632/widget.png?style=shield" alt="Discord Server">
  </a>
  <a href="https://www.python.org/downloads/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/Red-Discordbot">
  </a>
  <a href="https://github.com/BarcodeBimbo/Xbox-Web-Authorization/blob/main/xbox_api.py">
     <img src="https://img.shields.io/badge/html-python-red.svg" alt="xbox_api.py">
  </a>
</p>

# Xbox Live Authentication Web-App

This project provides a web-based authentication service for Xbox Live, allowing users to sign in, resolve their Xbox User IDs (XUIDs), and access related information.

## Features
- Sign in with Xbox Live using OAuth 2.0.
- View authentication status and access tokens.
- Resolve Xbox User IDs (XUID).
- Display user profile information, including gamertag and profile picture.

## Technologies Used
- HTML, CSS, Bootstrap for front-end design.
- Flask (Python) for back-end development.
- Waitress server for production deployment.
- REST APIs for Xbox Live integration.

---

### Preview:
<video src="https://github.com/user-attachments/assets/dda249d0-b1c1-4e59-8e8f-441cd3d5932f.mp4"></video>

## Installation and Setup

Follow these steps to set up and run the application locally:

### Prerequisites
1. Ensure you have the following installed:
   - Python 3.8 or later.
   - pip (Python package manager).
   - A modern web browser.

2. Clone this repository:
   ```bash
   git clone https://github.com/BarcodeBimbo/Xbox-Web-Authorization.git
   cd Xbox-Web-Authorization
   ```

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up an Xbox Live application to obtain your `CLIENT_ID` and configure the `REDIRECT_URI`:
   - Register your app at the [Microsoft Azure Portal](https://portal.azure.com/).
   - Use `http://127.0.0.1:666/oauth_success` as the redirect URI.

5. Update the Flask app configuration in the code:
   ```python
   CLIENT_ID = "your-client-id"
   REDIRECT_URI = "http://127.0.0.1:5965/oauth_success"
   ```

6. Create a directory for token storage:
   ```bash
   mkdir token_storage
   ```

### Running the App
1. Start the application:
   ```bash
   python xbox_api.py
   ```

2. Access the app in your browser at `http://127.0.0.1:5965`.

3. Follow the prompts to log in with your Xbox Live credentials.

---

## Deployment
For production deployment, the Waitress server is recommended:

1. Install Waitress:
   ```bash
   pip install waitress
   ```

2. Run the application with Waitress:
   ```bash
   waitress-serve --port=5965 xbox_api:XboxAPI
   ```

---

## Usage
### Login
1. On the home page, check the Terms of Service box.
2. Click the "Sign in with Xbox Live" button.

### XUID Resolution
1. After successful login, click the "Resolve XUID" button.
2. Copy the resolved XUID using the provided button.

### Logout
Click the "Logout" button to end your session.

---

## License
This project is licensed under the GNU General Public License. See the LICENSE file for more details.

## Disclaimer
This software is provided "as is" without warranty of any kind. The developers are not liable for any damages arising from its use. Use at your own risk.
