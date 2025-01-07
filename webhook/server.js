import express from "express";
import axios from "axios";
const app = express();
app.use(express.json());

const { VERIFY_TOKEN, ACCESS_TOKEN, PORT } = process.env;

app.post("/webhook", async (req, res) => {
  console.log("Full webhook payload:", JSON.stringify(req.body, null, 2));
  const message = req.body.entry?.[0]?.changes[0]?.value?.messages?.[0];
  
  if (message) {
    const business_phone_number_id =
      req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;

    // mark incoming message as read
    await axios({
      method: "POST",
      url: `https://graph.facebook.com/v20.0/${business_phone_number_id}/messages`,
      headers: {
        Authorization: `Bearer ${ACCESS_TOKEN}`,
      },
      data: {
        messaging_product: "whatsapp",
        status: "read",
        message_id: message.id,
      },
    });

    // Forward the message to Flask app via ngrok
    try {
      console.log("Attempting to forward message to Flask app");

      let forwardMessage = {
        from: message.from
      };

      switch (message.type) {
        case "text":
          forwardMessage.message = message.text.body;
          break;
        case "location":
          forwardMessage.location = {
            latitude: message.location.latitude,
            longitude: message.location.longitude,
            name: message.location.name,
            address: message.location.address,
          };
          break;
        case "audio":
          forwardMessage.audio = {
            url: message.audio.url,
            mime_type: message.audio.mime_type,
            id: message.audio.id
          };
          break;
      case "image":
        forwardMessage.image = {
          url: message.image.url,
          mime_type: message.image.mime_type,
          id: message.image.id,
          caption: message.image.caption
  };
          break;
        case "interactive":
          forwardMessage.interactive = {
            title: message.interactive.button_reply.title
          }
  break;
        default:
          console.log("Received unsupported message type");
      }

      if (forwardMessage.message || forwardMessage.location || forwardMessage.audio || forwardMessage.image || forwardMessage.interactive) {
        const response = await axios.post('http://flask-app:80/webhook', forwardMessage);
        console.log('Message forwarded to Flask app. Response:', response.data);
      } else {
        console.log("No valid message content to forward");
      }
    } catch (error) {
      console.error('Error forwarding message to Flask app:', error.message);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
    }
  } else {
    console.log("No message in webhook payload");
  }
  
  res.sendStatus(200);
});

app.get("/webhook", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    res.status(200).send(challenge);
    console.log("Webhook verified successfully!");
  } else {
    res.sendStatus(403);
  }
});

app.get("/", (req, res) => {
  res.send(`<pre>Nothing to see here.
Checkout README.md to start.</pre>`);
});

app.get("/test-flask", async (req, res) => {
  try {
    const response = await axios.post('http://flask-app:80/webhook', {
      message: "Test from Glitch",
      from: "Glitch"
    });
    res.send("Test message sent to Flask. Response: " + JSON.stringify(response.data));
  } catch (error) {
    res.status(500).send("Error: " + error.message);
  }
});

app.listen(PORT, () => {
  console.log(`Server is listening on port: ${PORT}`);
});
