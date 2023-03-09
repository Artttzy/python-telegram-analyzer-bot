import dotenv from 'dotenv';
import express from 'express';
import { logTelegramRedirect } from './handlers/mainHandler';
import cookieparser from 'cookie-parser';
dotenv.config();

const app = express();
app.use(cookieparser());
const port = process.env.PORT!;
app.get('/open', logTelegramRedirect);
app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});