from flask import Flask, request, render_template_string
import requests
import json

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def send_whatsapp():
    if request.method == 'POST' and 'client_phone' in request.form:
        recipient_contact = request.form['client_phone']
        url = "https://graph.facebook.com/v19.0/230797580115839/messages"
        authorization = "Bearer EAAJSrKZBQAMYBO5SkE4Kqf3sXLDhiUU2imVyhNyswkUZCOtcWZC02ZAUUf3RpuFVqe8NWe16Gu7OpZBtFkvsJiwA9VtzOL9hN7sW9epqU5t9x6xkjOtweWePZCpZCSP1S4CdU0ZBPpQrfRMSb9TqG1B3s4eJpqLQwcegaGWkzpUlikE7RbHfPxK4hQ0yMOSbQoQZBYgZDZD"
        content_type = "application/json"

        # Define the parameters for the head and body sections
        client_name = request.form['client_name']

        head_parameters = [
            {
                "type": "text",
                "parameter_name": "client_name",
                "text": client_name
            }
        ]

        app_name = request.form['app_name']
        app_download_url = request.form['app_download_url']
        username = request.form['username']
        password = request.form['password']
        day = request.form['day']
        month = request.form['month']
        year = request.form['year']
        company_name = request.form['company_name']

        body_parameters = [
            {
                "type": "text",
                "parameter_name": "app_name",
                "text": app_name
            },
            {
                "type": "text",
                "parameter_name": "app_download_url",
                "text": app_download_url
            },
            {
                "type": "text",
                "parameter_name": "username",
                "text": username
            },
            {
                "type": "text",
                "parameter_name": "password",
                "text": password
            },
            {
                "type": "text",
                "parameter_name": "day",
                "text": day
            },
            {
                "type": "text",
                "parameter_name": "month",
                "text": month
            },
            {
                "type": "text",
                "parameter_name": "year",
                "text": year
            },
            {
                "type": "text",
                "parameter_name": "company_name",
                "text": company_name
            }
        ]

        # Define the button parameters (commented out in original code)
        button_parameters = [
            {
                "type": "text",
                "text": "smb_filedownloader3.php?user_id=1&ftp=hellothere&timestamp=173434"
            }
        ]

        data = {
            "messaging_product": "whatsapp",
            "to": recipient_contact,
            "type": "template",
            "template": {
                "name": "ginger_wifi_iptv_utility_en",
                "language": {
                    "code": "en"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": head_parameters
                    },
                    {
                        "type": "body",
                        "parameters": body_parameters
                    }
                    # Button component is commented out in original code
                    # {
                    #     "type": "button",
                    #     "sub_type": "url",
                    #     "index": "0",
                    #     "parameters": button_parameters
                    # }
                ]
            }
        }

        headers = {
            "Authorization": authorization,
            "Content-Type": content_type
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code != 200:
            return f'Error: {response.text}'
        else:
            # Return success HTML page
            success_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Message Sent</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .popup {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                        text-align: center;
                    }
                    .popup h2 {
                        color: green;
                    }
                    .close-btn {
                        background: green;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        cursor: pointer;
                        margin-top: 15px;
                        border-radius: 5px;
                    }
                </style>
                <script>
                    function startCountdown() {
                        let count = 5;
                        const countdownElement = document.getElementById("countdown");
                        const interval = setInterval(() => {
                            countdownElement.textContent = count;
                            count--;
                            if (count < 0) {
                                clearInterval(interval);
                                window.location.href = 'index.html';
                            }
                        }, 1000);
                    }
                </script>
            </head>
            <body>
                <div class="popup">
                    <h2>Success!</h2>
                    <p>Your WhatsApp message has been sent successfully.</p>
                    <p>Redirecting in <span id="countdown">5</span> seconds...</p>
                    <button class="close-btn" onclick="startCountdown()">Close</button>
                </div>
            </body>
            </html>
            """
            return render_template_string(success_html)

    return "Please submit the form with client_phone and other required fields."


if __name__ == '__main__':
    app.run(debug=True)